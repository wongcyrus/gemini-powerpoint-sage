"""Tests for video file management helpers."""

from pathlib import Path
from unittest.mock import patch

import pytest

from core.domain.video_synthesis import VideoSynthesisError
from services.video_synthesis.file_manager import ConcurrentFileManager, VideoFileManager


class TestVideoFileManager:
    """Tests for VideoFileManager."""

    def test_initializes_cache_and_temp_dirs(self, tmp_path):
        """Manager should set up cache and temp directories."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-1")

        assert manager.temp_dir.exists()
        assert manager.cache_dir.exists()
        assert manager.operation_id == "op-1"

    def test_generate_segment_cache_key_is_stable(self, tmp_path):
        """Cache keys should change when inputs change and include slide index."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-2")
        image = tmp_path / "slide_1.png"
        audio = tmp_path / "slide_1.mp3"
        image.write_bytes(b"image")
        audio.write_bytes(b"audio")

        key1 = manager.generate_segment_cache_key(image, audio, {"fps": 30}, slide_index=1)
        key2 = manager.generate_segment_cache_key(image, audio, {"fps": 30}, slide_index=1)
        key3 = manager.generate_segment_cache_key(image, audio, {"fps": 60}, slide_index=1)

        assert key1 == key2
        assert key1 != key3
        assert key1.startswith("1_")

    def test_generate_segment_cache_key_uses_paths_when_files_missing(self, tmp_path):
        """Missing inputs should still produce stable keys from the paths."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-2b")
        image = tmp_path / "missing_slide.png"
        audio = tmp_path / "missing_slide.mp3"

        key = manager.generate_segment_cache_key(image, audio, {"fps": 30}, slide_index=2)

        assert key.startswith("2_")

    def test_cache_and_retrieve_segment(self, tmp_path):
        """Segments should be cached and discovered by key."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-3")
        source = tmp_path / "segment.mp4"
        source.write_bytes(b"video-bytes")

        cached = manager.cache_segment(source, "1_deadbeef")
        assert cached.exists()
        assert manager.get_cached_segment("1_deadbeef") == cached

    def test_cache_stats_and_clear(self, tmp_path):
        """Cache stats and cleanup should reflect stored files."""
        cache_dir = tmp_path / "cache"
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-4", cache_dir=cache_dir)
        cached = manager.cache_dir / "slide_1_deadbeef.mp4"
        cached.write_bytes(b"abc")

        stats = manager.get_cache_stats()
        assert stats["cache_enabled"] is True
        assert stats["cached_segments"] == 1

        cleanup = manager.clear_cache()
        assert cleanup["files_removed"] >= 1

    def test_cache_stats_missing_dir_and_clear_skips_newer_files(self, tmp_path):
        """Missing cache directories should report disabled and newer files should be preserved."""
        cache_dir = tmp_path / "cache"
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-4b", cache_dir=cache_dir)
        fresh = manager.cache_dir / "slide_1_new.mp4"
        fresh.write_bytes(b"new")

        missing_manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-4c", cache_dir=tmp_path / "missing-cache")
        missing_manager.cache_dir.rmdir()
        assert missing_manager.get_cache_stats() == {"cache_enabled": False}

        import os, time
        future_time = time.time() + 24 * 3600
        os.utime(fresh, (future_time, future_time))

        cleanup = manager.clear_cache(older_than_days=1)
        assert cleanup["files_removed"] == 0
        assert fresh.exists() is True

    def test_output_operations(self, tmp_path):
        """Output helpers should copy and move files."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-5")
        source = manager.get_temp_file_path("source.mp4")
        source.write_bytes(b"video")
        copy_dest = tmp_path / "out" / "copy.mp4"
        move_dest = tmp_path / "final" / "move.mp4"

        copied = manager.copy_to_output(source, copy_dest)
        assert copied.exists()
        assert copied.read_bytes() == b"video"

        moved = manager.move_to_output(source, move_dest)
        assert moved.exists()
        assert not source.exists()

    def test_ensure_output_directory_rejects_non_writable(self, tmp_path):
        """Non-writable output directories should fail fast."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-5b")
        output_path = tmp_path / "out" / "video.mp4"

        with patch("os.access", return_value=False):
            with pytest.raises(VideoSynthesisError, match="Failed to ensure output directory"):
                manager.ensure_output_directory(output_path)

    def test_cleanup_immediately_can_be_disabled(self, tmp_path):
        """Immediate cleanup should respect configuration."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-6")
        temp_file = manager.get_temp_file_path("temp.txt")
        temp_file.write_text("x")

        with patch("services.video_synthesis.file_manager.CleanupConfig.should_cleanup_immediately", return_value=False):
            manager._cleanup_temp_files_immediately()

        assert temp_file.exists()

    def test_disk_usage_and_registry_cleanup(self, tmp_path):
        """Disk usage and global cleanup should reflect tracked managers."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-7")
        tracked = manager.get_temp_file_path("tracked.bin")
        tracked.write_bytes(b"12345")

        usage = manager.get_disk_usage()
        assert usage["temp_files_count"] == 1
        assert usage["temp_files_size_bytes"] == 5

    def test_get_disk_usage_handles_statvfs_failure(self, tmp_path):
        """Disk usage should degrade gracefully when statvfs fails."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-7b")
        with patch("os.statvfs", side_effect=OSError("boom")):
            usage = manager.get_disk_usage()

        assert usage["temp_files_count"] == 0
        assert usage["available_space_bytes"] == 0

        stats = VideoFileManager.cleanup_all_active()
        assert stats["managers_cleaned"] >= 1

    def test_subdirectories_and_cache_fallbacks(self, tmp_path):
        """Subdirectory creation and cache lookup fallbacks should work."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-8", cache_dir=tmp_path / "cache")
        subfile = manager.get_temp_file_path("note.txt", subdirectory="sub")
        segment_dir = manager.create_segment_temp_dir()
        working_dir = manager.create_working_temp_dir("processing")
        cached = manager.get_cached_segment("1_deadbeef")

        assert subfile.parent == tmp_path / f"video_synthesis_{manager.operation_id}" / "sub"
        assert segment_dir.exists()
        assert working_dir.exists()
        assert cached is None

    def test_get_cached_segment_invalid_key_returns_none(self, tmp_path):
        """Invalid cache keys should not resolve to a cached segment."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-8c", cache_dir=tmp_path / "cache")
        assert manager.get_cached_segment("not-a-key") is None

    def test_cache_dir_derives_from_audio_dir(self, tmp_path):
        """Audio directory inputs should derive a presentation-specific cache dir."""
        audio_dir = tmp_path / "project_speech"
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-8b", enable_cache=False, audio_dir=audio_dir)

        assert manager.cache_dir == tmp_path / "project_segments"

    def test_cache_segment_disabled_and_get_cache_stats_missing_dir(self, tmp_path):
        """Disabled cache should return original files and missing dirs should report disabled."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-9", enable_cache=False)
        source = tmp_path / "segment.mp4"
        source.write_bytes(b"video")

        assert manager.cache_segment(source, "key") == source
        assert manager.get_cache_stats() == {"cache_enabled": False}

    def test_cleanup_temp_files_preserves_cached_segments(self, tmp_path):
        """Immediate cleanup should remove temp files but preserve cached ones."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-9b")
        temp_file = manager.get_temp_file_path("temp.txt")
        temp_file.write_text("x")
        cached_file = manager.cache_dir / "slide_1_cache.mp4"
        cached_file.write_bytes(b"cache")
        manager.created_files.append(cached_file)

        with patch("services.video_synthesis.file_manager.CleanupConfig.should_cleanup_immediately", return_value=True), patch(
            "services.video_synthesis.file_manager.CleanupConfig.CLEANUP_EMPTY_DIRS", False
        ), patch(
            "services.video_synthesis.file_manager.CleanupConfig.LOG_DISK_USAGE", False
        ):
            manager._cleanup_temp_files_immediately()

        assert not temp_file.exists()
        assert cached_file.exists()

    def test_clear_cache_and_cleanup_manager_registry(self, tmp_path):
        """Cleanup helpers should remove old cached files and clear active managers."""
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-10")
        old_file = manager.cache_dir / "slide_1_old.mp4"
        new_file = manager.cache_dir / "slide_2_new.mp4"
        old_file.write_bytes(b"old")
        new_file.write_bytes(b"new")

        # Make the old file appear stale.
        import os, time
        stale_time = time.time() - (3 * 24 * 3600)
        os.utime(old_file, (stale_time, stale_time))

        stats = manager.clear_cache(older_than_days=1)
        assert stats["files_removed"] >= 1
        assert old_file.exists() is False
        assert new_file.exists() is True

        all_stats = VideoFileManager.cleanup_all_active()
        assert all_stats["managers_cleaned"] >= 1

    def test_get_cached_segment_falls_back_to_slide_prefix(self, tmp_path):
        """Cache lookup should reuse any existing segment for the same slide."""
        cache_dir = tmp_path / "cache"
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-11", cache_dir=cache_dir)
        existing = manager.cache_dir / "slide_2_existing.mp4"
        existing.write_bytes(b"cached")

        cached = manager.get_cached_segment("2_deadbeef")

        assert cached == existing

    def test_concurrent_file_manager_lifecycle(self, tmp_path):
        """Concurrent manager should create, track, and clean up operations."""
        manager = ConcurrentFileManager(base_temp_dir=tmp_path)

        op_manager = manager.create_operation_manager("operation-1")
        assert manager.get_operation_manager("operation-1") == op_manager

        status = manager.get_all_operations_status()
        assert "operation-1" in status
        assert status["operation-1"]["cleanup_completed"] is False

        cleanup = manager.cleanup_operation("operation-1")
        assert cleanup.get("already_cleaned") is not True
        assert manager.get_operation_manager("operation-1") is None

        missing = manager.cleanup_operation("missing-operation")
        assert missing == {"error": "Operation not found"}

    def test_concurrent_file_manager_cleanup_all_operations(self, tmp_path):
        """Cleaning all operations should empty the registry."""
        manager = ConcurrentFileManager(base_temp_dir=tmp_path)
        manager.create_operation_manager("operation-2")
        manager.create_operation_manager("operation-3")

        stats = manager.cleanup_all_operations()

        assert stats["operations_cleaned"] == 2
        assert manager.get_all_operations_status() == {}
