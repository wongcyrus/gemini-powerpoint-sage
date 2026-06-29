"""Tests for video combination helpers."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.domain.video_synthesis import FileValidationError, VideoProcessingError
from services.video_synthesis.video_combine_helpers import (
    build_concat_command,
    build_normalized_concat_command,
    calculate_total_video_duration,
    validate_video_paths,
)


class TestVideoCombineHelpers:
    """Tests for combination prep helpers."""

    def test_validate_video_paths_requires_existing_files(self, tmp_path):
        """Missing or non-file paths should fail fast."""
        video = tmp_path / "a.mp4"
        video.write_bytes(b"video")
        validate_video_paths([video])

        with pytest.raises(FileValidationError, match="Video file not found"):
            validate_video_paths([tmp_path / "missing.mp4"])

    def test_calculate_total_video_duration_sums_ffprobe_output(self, tmp_path):
        """Duration probing should sum parsed ffprobe values."""
        video1 = tmp_path / "a.mp4"
        video2 = tmp_path / "b.mp4"
        video1.write_bytes(b"1")
        video2.write_bytes(b"2")

        def fake_run(cmd, capture_output, text, timeout):
            return Mock(returncode=0, stdout="1.5")

        with patch("services.video_synthesis.video_combine_helpers.subprocess.run", side_effect=fake_run):
            total = calculate_total_video_duration([video1, video2])

        assert total == 3.0

    def test_calculate_total_video_duration_raises_on_bad_probe(self, tmp_path):
        """Bad probe output should surface as processing errors."""
        video = tmp_path / "a.mp4"
        video.write_bytes(b"1")

        with patch(
            "services.video_synthesis.video_combine_helpers.subprocess.run",
            return_value=Mock(returncode=0, stdout="not-a-number"),
        ):
            with pytest.raises(VideoProcessingError, match="Failed to analyze video"):
                calculate_total_video_duration([video])

    def test_build_concat_command_formats_ffmpeg_args(self, tmp_path):
        """Concat command should target the concat demuxer."""
        concat_file = tmp_path / "concat.txt"
        output = tmp_path / "out.mp4"

        command = build_concat_command(concat_file, output)

        assert command[:5] == ["ffmpeg", "-y", "-f", "concat", "-safe"]
        assert command[-1] == str(output)

    def test_build_normalized_concat_command_adds_audio_and_video_filters(self, tmp_path):
        """Normalized concat should re-encode to a shared format."""
        clip1 = tmp_path / "a.mp4"
        clip2 = tmp_path / "b.mp4"
        output = tmp_path / "out.mp4"
        config = Mock(resolution=(1920, 1080), fps=30, video_codec="libx264", audio_codec="aac", video_bitrate="2M", audio_bitrate="128k", output_format="mp4")

        command = build_normalized_concat_command([clip1, clip2], output, config)

        assert command[:3] == ["ffmpeg", "-y", "-i"]
        assert str(clip1) in command and str(clip2) in command
        assert "-filter_complex" in command
        assert "aformat=sample_rates=48000:channel_layouts=stereo" in " ".join(command)
        assert "-ac" in command and "2" in command
        assert command[-1] == str(output)
