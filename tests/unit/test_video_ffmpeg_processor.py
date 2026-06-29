"""Tests for direct FFmpeg processing helpers."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from core.domain.video_synthesis import SlideVideoSegment, VideoConfig, VideoProcessingError
from services.video_synthesis.ffmpeg_processor import FFmpegVideoProcessor
from services.video_synthesis.file_manager import VideoFileManager


class TestFFmpegVideoProcessor:
    """Tests for FFmpegVideoProcessor."""

    def test_build_cache_config(self):
        """Cache config should include the deterministic segment inputs."""
        processor = FFmpegVideoProcessor()
        config = VideoConfig(resolution=(1280, 720), fps=24, output_format="webm")

        cache_config = processor._build_cache_config(config)

        assert cache_config["resolution"] == (1280, 720)
        assert cache_config["fps"] == 24
        assert cache_config["output_format"] == "webm"

    def test_format_specific_options(self):
        """Format helpers should return encoding options per format."""
        processor = FFmpegVideoProcessor()
        assert processor._get_format_specific_options(VideoConfig(output_format="mp4"))["movflags"] == "+faststart"
        assert processor._get_format_specific_options(VideoConfig(output_format="webm"))["deadline"] == "good"
        assert processor._get_format_specific_options(VideoConfig(output_format="avi")) == {}

    def test_get_video_info(self, tmp_path):
        """Video info should be parsed from ffprobe output."""
        video = tmp_path / "out.mp4"
        video.write_bytes(b"video")
        probe = {
            "format": {"duration": "5.5", "size": "100", "format_name": "mp4", "bit_rate": "2000"},
            "streams": [
                {"codec_type": "video", "width": 1920, "height": 1080, "codec_name": "h264", "r_frame_rate": "30/1", "bit_rate": "1500"},
                {"codec_type": "audio", "codec_name": "aac", "sample_rate": "44100", "channels": 2, "bit_rate": "500"},
            ],
        }

        with patch("subprocess.run", return_value=Mock(returncode=0, stdout=json.dumps(probe), stderr="")):
            info = FFmpegVideoProcessor().get_video_info(video)

        assert info["duration_seconds"] == 5.5
        assert info["width"] == 1920
        assert info["audio_codec"] == "aac"

    def test_concatenate_segments_single_and_multiple(self, tmp_path):
        """Concatenation should handle single and multi-segment flows."""
        processor = FFmpegVideoProcessor(temp_dir=tmp_path)
        config = VideoConfig()
        segment1 = tmp_path / "segment_001.mp4"
        segment2 = tmp_path / "segment_002.mp4"
        segment1.write_bytes(b"1")
        segment2.write_bytes(b"2")
        single_output = tmp_path / "single.mp4"
        multi_output = tmp_path / "multi.mp4"
        segs_single = [Mock(temp_video_path=segment1, duration_seconds=1.0)]
        segs_multi = [Mock(temp_video_path=segment1, duration_seconds=1.0), Mock(temp_video_path=segment2, duration_seconds=1.0)]

        def fake_run(cmd, capture_output, text, timeout=None, cwd=None):
            output = Path(cmd[-1])
            output.write_bytes(b"done")
            return Mock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            single = processor.concatenate_segments(segs_single, config, single_output, tmp_path)
            multi = processor.concatenate_segments(segs_multi, config, multi_output, tmp_path)

        assert single == single_output
        assert multi == multi_output

    def test_concatenate_video_files_orders_clips(self, tmp_path):
        """Pre-rendered clip concatenation should preserve the provided order."""
        processor = FFmpegVideoProcessor(temp_dir=tmp_path)
        config = VideoConfig()
        clip1 = tmp_path / "clip1.mp4"
        clip2 = tmp_path / "clip2.mp4"
        clip1.write_bytes(b"1")
        clip2.write_bytes(b"2")
        output = tmp_path / "combined.mp4"

        def fake_run(cmd, capture_output, text, timeout=None, cwd=None):
            Path(cmd[-1]).write_bytes(b"done")
            return Mock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            result = processor.concatenate_video_files([clip1, clip2], config, output, tmp_path)

        assert result == output
        assert output.exists()

    def test_create_video_segment_uses_cache(self, tmp_path):
        """Cached segments should be returned without running ffmpeg."""
        processor = FFmpegVideoProcessor(temp_dir=tmp_path)
        image = tmp_path / "slide_1.png"
        audio = tmp_path / "slide_1.mp3"
        image.write_bytes(b"img")
        audio.write_bytes(b"aud")
        segment = SlideVideoSegment(1, image, audio, 1.0)
        config = VideoConfig()
        manager = VideoFileManager(base_temp_dir=tmp_path, operation_id="op-cache")
        cached = manager.cache_dir / "slide_1_deadbeef.mp4"
        cached.write_bytes(b"cached")

        with patch.object(manager, "generate_segment_cache_key", return_value="1_deadbeef"), patch.object(
            manager, "get_cached_segment", return_value=cached
        ), patch("subprocess.run") as mock_run:
            result = processor.create_video_segment(segment, config, tmp_path, manager)

        assert result == cached
        assert segment.temp_video_path == cached
        mock_run.assert_not_called()

    def test_create_video_segment_failure(self, tmp_path):
        """FFmpeg failures should raise processing errors."""
        processor = FFmpegVideoProcessor(temp_dir=tmp_path)
        image = tmp_path / "slide_2.png"
        audio = tmp_path / "slide_2.mp3"
        image.write_bytes(b"img")
        audio.write_bytes(b"aud")
        segment = SlideVideoSegment(2, image, audio, 1.0)

        with patch("subprocess.run", return_value=Mock(returncode=1, stdout="", stderr="boom")):
            try:
                processor.create_video_segment(segment, VideoConfig(), tmp_path)
            except VideoProcessingError as exc:
                assert "segment" in str(exc).lower()
            else:  # pragma: no cover
                raise AssertionError("Expected VideoProcessingError")

    def test_concatenate_segments_rejects_empty_and_missing_files(self, tmp_path):
        """Concatenation should reject empty inputs and missing temp paths."""
        processor = FFmpegVideoProcessor(temp_dir=tmp_path)
        output = tmp_path / "out.mp4"

        with patch("subprocess.run"):
            try:
                processor.concatenate_segments([], VideoConfig(), output, tmp_path)
            except VideoProcessingError as exc:
                assert "No video segments" in str(exc)
            else:  # pragma: no cover
                raise AssertionError("Expected VideoProcessingError")

        missing = Mock(temp_video_path=tmp_path / "missing.mp4", duration_seconds=1.0)
        with patch("subprocess.run"):
            try:
                processor.concatenate_segments([missing], VideoConfig(), output, tmp_path)
            except VideoProcessingError as exc:
                assert "Missing video segment file" in str(exc)
            else:  # pragma: no cover
                raise AssertionError("Expected VideoProcessingError")

    def test_concatenate_segments_single_segment_timeout_and_success(self, tmp_path):
        """Single-segment concatenation should surface timeout and success branches."""
        processor = FFmpegVideoProcessor(temp_dir=tmp_path)
        config = VideoConfig()
        segment_path = tmp_path / "segment_001.mp4"
        segment_path.write_bytes(b"seg")
        segment = Mock(temp_video_path=segment_path, duration_seconds=1.0)
        output = tmp_path / "out.mp4"

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=60)):
            try:
                processor.concatenate_segments([segment], config, output, tmp_path)
            except VideoProcessingError as exc:
                assert "timed out" in str(exc)
            else:  # pragma: no cover
                raise AssertionError("Expected VideoProcessingError")

        def fake_run(cmd, capture_output, text, timeout=None):
            Path(cmd[-1]).write_bytes(b"out")
            return Mock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            result = processor.concatenate_segments([segment], config, output, tmp_path)

        assert result == output

    def test_concatenate_simple_falls_back_to_emergency_video(self, tmp_path):
        """Fallback concatenation should reach the emergency-video branch."""
        processor = FFmpegVideoProcessor(temp_dir=tmp_path)
        config = VideoConfig()
        segment_path = tmp_path / "segment_001.mp4"
        segment_path.write_bytes(b"seg")
        output = tmp_path / "out.mp4"
        segment = Mock(temp_video_path=segment_path, duration_seconds=1.0)

        with patch.object(processor, "_concatenate_with_demuxer", side_effect=RuntimeError("demuxer")), patch.object(
            processor, "_concatenate_with_filter_complex", side_effect=RuntimeError("filter")
        ), patch.object(processor, "_create_emergency_video") as emergency:
            processor._concatenate_simple([segment], config, output, tmp_path)

        emergency.assert_called_once()

    def test_demuxer_chunked_and_info_branches(self, tmp_path):
        """Demuxer chunking and video-info edge cases should be covered."""
        processor = FFmpegVideoProcessor(temp_dir=tmp_path)
        config = VideoConfig()
        output = tmp_path / "out.mp4"
        segments = []
        for i in range(51):
            path = tmp_path / f"segment_{i:03d}.mp4"
            path.write_bytes(b"seg")
            segments.append(Mock(temp_video_path=path, duration_seconds=1.0))

        with patch.object(processor, "_concatenate_chunked") as chunked:
            processor._concatenate_with_demuxer(segments, config, output, tmp_path)

        chunked.assert_called_once()

        video = tmp_path / "video.mp4"
        video.write_bytes(b"video")
        probe = {"format": {"duration": "1.0", "size": "5"}, "streams": [{"codec_type": "video", "r_frame_rate": "a/b"}]}
        with patch("subprocess.run", return_value=Mock(returncode=0, stdout=json.dumps(probe), stderr="")):
            info = processor.get_video_info(video)
        assert info["fps"] == 0
        assert "audio_codec" not in info

        with patch("subprocess.run", return_value=Mock(returncode=1, stdout="", stderr="boom")):
            try:
                processor.get_video_info(video)
            except VideoProcessingError as exc:
                assert "FFprobe failed" in str(exc)
            else:  # pragma: no cover
                raise AssertionError("Expected VideoProcessingError")
