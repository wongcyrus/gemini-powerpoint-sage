"""Tests for video validation utilities."""

import json
from pathlib import Path

from utils.video_validator import (
    VideoValidator,
    should_skip_video_synthesis,
    validate_video_file,
)


class TestVideoValidator:
    """Tests for VideoValidator helpers."""

    def test_get_video_info_parses_video_and_audio_streams(self, monkeypatch, tmp_path):
        """FFprobe JSON should be converted into a rich info dictionary."""
        video_path = tmp_path / "video.mp4"
        video_path.touch()

        class Result:
            returncode = 0
            stderr = ""
            stdout = json.dumps(
                {
                    "format": {
                        "duration": "12.5",
                        "size": "2048",
                        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                    },
                    "streams": [
                        {
                            "codec_type": "video",
                            "width": 1920,
                            "height": 1080,
                            "codec_name": "h264",
                            "r_frame_rate": "30/1",
                            "bit_rate": "800000",
                        },
                        {
                            "codec_type": "audio",
                            "codec_name": "aac",
                            "sample_rate": "48000",
                            "channels": "2",
                        },
                    ],
                }
            )

        monkeypatch.setattr("utils.video_validator.subprocess.run", lambda *args, **kwargs: Result())

        info = VideoValidator.get_video_info(video_path)

        assert info["duration_seconds"] == 12.5
        assert info["has_video"] is True
        assert info["has_audio"] is True
        assert info["width"] == 1920
        assert info["height"] == 1080
        assert info["video_codec"] == "h264"
        assert info["audio_codec"] == "aac"
        assert info["channels"] == 2

    def test_get_video_info_returns_none_on_ffprobe_failure(self, monkeypatch, tmp_path):
        """Non-zero ffprobe exits should be treated as a failure."""
        video_path = tmp_path / "broken.mp4"
        video_path.touch()

        class Result:
            returncode = 1
            stderr = "ffprobe failed"
            stdout = ""

        monkeypatch.setattr("utils.video_validator.subprocess.run", lambda *args, **kwargs: Result())

        assert VideoValidator.get_video_info(video_path) is None

    def test_estimate_expected_duration_sums_successful_audio_durations(self, monkeypatch, tmp_path):
        """Audio durations should be summed from ffprobe output."""
        audio1 = tmp_path / "a1.mp3"
        audio2 = tmp_path / "a2.mp3"
        audio1.touch()
        audio2.touch()

        class Result:
            returncode = 0
            stdout = "3.5\n"

        monkeypatch.setattr("utils.video_validator.subprocess.run", lambda *args, **kwargs: Result())

        assert VideoValidator.estimate_expected_duration([audio1, audio2]) == 7.0

    def test_estimate_expected_duration_uses_size_fallback_when_ffprobe_fails(self, monkeypatch, tmp_path):
        """A failed probe should fall back to size-based duration estimation."""
        audio = tmp_path / "fallback.mp3"
        audio.write_bytes(b"x" * 1024 * 1024)

        class Result:
            returncode = 1
            stdout = ""

        monkeypatch.setattr("utils.video_validator.subprocess.run", lambda *args, **kwargs: Result())

        assert VideoValidator.estimate_expected_duration([audio]) == 8.0

    def test_validate_video_file_delegates_to_class_validator(self, monkeypatch):
        """The convenience wrapper should call the class validator with a Path."""
        seen = {}

        def fake_is_valid(video_path, min_size_mb=1.0, min_duration_seconds=5.0):
            seen["path"] = video_path
            seen["min_size_mb"] = min_size_mb
            seen["min_duration_seconds"] = min_duration_seconds
            return True

        monkeypatch.setattr(VideoValidator, "is_valid_video", staticmethod(fake_is_valid))

        assert validate_video_file("/tmp/video.mp4", min_size_mb=2.5, min_duration_seconds=9.0) is True
        assert seen["path"] == Path("/tmp/video.mp4")
        assert seen["min_size_mb"] == 2.5
        assert seen["min_duration_seconds"] == 9.0

    def test_should_skip_video_synthesis_returns_false_when_output_missing(self):
        """Missing outputs should always trigger synthesis."""
        assert should_skip_video_synthesis("/tmp/missing.mp4", []) is False

    def test_should_skip_synthesis_returns_true_for_valid_existing_video(self, monkeypatch, tmp_path):
        """A valid existing video should skip regeneration."""
        output = tmp_path / "existing.mp4"
        output.touch()
        audio = tmp_path / "audio.mp3"
        audio.touch()

        monkeypatch.setattr(VideoValidator, "estimate_expected_duration", staticmethod(lambda files: 10.0))
        monkeypatch.setattr(VideoValidator, "is_valid_video", staticmethod(lambda *args, **kwargs: True))
        monkeypatch.setattr(
            VideoValidator,
            "get_video_info",
            staticmethod(lambda path: {"duration_seconds": 10.5, "file_size_bytes": 2 * 1024 * 1024}),
        )

        assert VideoValidator.should_skip_synthesis(output, [audio]) is True

    def test_should_skip_synthesis_returns_false_for_invalid_existing_video(self, monkeypatch, tmp_path):
        """Invalid videos should be regenerated."""
        output = tmp_path / "existing.mp4"
        output.touch()
        audio = tmp_path / "audio.mp3"
        audio.touch()

        monkeypatch.setattr(VideoValidator, "estimate_expected_duration", staticmethod(lambda files: 10.0))
        monkeypatch.setattr(VideoValidator, "is_valid_video", staticmethod(lambda *args, **kwargs: False))

        assert VideoValidator.should_skip_synthesis(output, [audio]) is False
