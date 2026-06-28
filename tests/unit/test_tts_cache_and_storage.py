"""Tests for TTS cache and storage helpers."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from core.domain.tts import PresentationType, StyleContext, VoiceConfig
from config.tts_config import TTSCacheConfig, TTSStorageConfig
from services.tts.cache_manager import CacheManager
from services.tts.storage_manager import StorageManager


class TestTTSCacheManager:
    """Tests for cache manager helpers."""

    def test_generate_cache_key_is_stable(self, tmp_path):
        """Normalization and ordering should make cache keys stable."""
        manager = CacheManager(TTSCacheConfig(cache_directory=str(tmp_path / "cache")))
        style = StyleContext(
            emphasis_words=["beta", "alpha"],
            emotional_indicators=["joy", "focus"],
            presentation_type=PresentationType.BUSINESS,
        )
        voice = VoiceConfig(language_code="en-US", voice_name="Aoede")

        key1 = manager.generate_cache_key(" Hello   world ", style, voice, "en-US")
        key2 = manager.generate_cache_key("Hello world", style, voice, "en-US")

        assert key1 == key2

    def test_cleanup_and_stats(self, tmp_path):
        """Expired files should be cleaned and stats should reflect remaining files."""
        manager = CacheManager(TTSCacheConfig(cache_directory=str(tmp_path / "cache"), ttl_hours=1))
        old_dir = tmp_path / "old"
        current_dir = tmp_path / "current"
        old_dir.mkdir()
        current_dir.mkdir()

        old_file = old_dir / "old.mp3"
        current_file = current_dir / "current.mp3"
        old_file.write_bytes(b"old")
        current_file.write_bytes(b"new")

        import os, time

        stale_time = time.time() - (2 * 3600)
        os.utime(old_file, (stale_time, stale_time))

        cleaned = manager.cleanup_expired_files([tmp_path])
        stats = manager.get_cache_stats([tmp_path])

        assert cleaned >= 1
        assert stats["total_files"] == 1


class TestTTSStorageManager:
    """Tests for storage manager helpers."""

    def test_paths_and_file_operations(self, tmp_path):
        """Storage helpers should build paths and manage local files."""
        storage = StorageManager(
            TTSStorageConfig(bucket_name="bucket", local_cache_dir=str(tmp_path / "speech")),
            main_config=SimpleNamespace(
                pptx_path=str(tmp_path / "deck.pptx"),
                pdf_path=str(tmp_path / "deck.pdf"),
                output_dir=str(tmp_path),
                style="professional",
            ),
        )

        directory = storage.generate_speech_directory_path("deck", "en-US")
        filename = storage.generate_audio_filename(2, "abcdef123456")
        audio_path = storage.get_audio_file_path("deck", "en-US", 2, "abcdef123456")

        assert "deck_en-US_speech" in directory
        assert filename == "slide_2_abcdef12.mp3"
        assert audio_path.endswith(filename)

    @pytest.mark.asyncio
    async def test_save_migrate_upload_and_cleanup_stats(self, tmp_path):
        """Saving, migrating, uploading, and cleanup stats should all work."""
        storage = StorageManager(TTSStorageConfig(bucket_name="bucket", local_cache_dir=str(tmp_path / "speech")))
        audio_path = tmp_path / "output" / "slide_1_abc.mp3"
        migrated_path = tmp_path / "migrated" / "slide_1_abc.mp3"

        saved_path = await storage.save_audio_file(b"audio-bytes", str(audio_path))
        migrated_path_result = await storage.migrate_audio_file(str(audio_path), str(migrated_path))

        assert Path(saved_path).exists()
        assert Path(migrated_path_result).exists()
        assert await storage.upload_audio_file(str(migrated_path_result), "remote/path") == f"file://{migrated_path_result}"

        stats = storage.get_storage_stats()
        assert stats["bucket_name"] == "bucket"
