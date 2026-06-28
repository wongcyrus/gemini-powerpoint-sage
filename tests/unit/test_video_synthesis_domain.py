"""Tests for video synthesis domain models."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.domain.video_synthesis import (
    AudioAnalysisError,
    FileValidationError,
    SlideVideoSegment,
    VideoConfig,
    VideoConfigurationError,
    VideoProcessingError,
    VideoSynthesisError,
    VideoSynthesisRequest,
    VideoSynthesisResult,
)


class TestVideoConfig:
    """Tests for VideoConfig validation."""

    def test_validate_accepts_valid_config(self):
        """Default config should validate successfully."""
        assert VideoConfig().validate() is None

    @pytest.mark.parametrize(
        "kwargs, message",
        [
            ({"resolution": (0, 1080)}, "Resolution must have positive width and height"),
            ({"fps": 0}, "FPS must be positive"),
            ({"fade_duration": -1}, "Fade duration cannot be negative"),
            ({"video_codec": "bad"}, "Video codec must be one of"),
            ({"audio_codec": "bad"}, "Audio codec must be one of"),
            ({"output_format": "bad"}, "Output format must be one of"),
        ],
    )
    def test_validate_rejects_invalid_config(self, kwargs, message):
        """Invalid values should raise a validation error."""
        with pytest.raises(ValueError, match=message):
            VideoConfig(**kwargs).validate()


class TestSlideVideoSegment:
    """Tests for slide-video segments."""

    def test_post_init_and_format_validation(self, tmp_path):
        """Segments should normalize paths and validate supported formats."""
        image = tmp_path / "slide_1.png"
        audio = tmp_path / "slide_1.mp3"
        image.touch()
        audio.touch()

        segment = SlideVideoSegment(1, str(image), str(audio), 1.5)

        assert segment.image_path == image
        assert segment.audio_path == audio
        segment.validate_formats()

    def test_post_init_rejects_missing_files(self, tmp_path):
        """Missing files should fail fast."""
        with pytest.raises(ValueError, match="Image file not found"):
            SlideVideoSegment(1, tmp_path / "missing.png", tmp_path / "audio.mp3", 1.0)

    def test_get_audio_duration_uses_ffprobe(self, tmp_path):
        """Audio duration extraction should parse ffprobe output."""
        audio = tmp_path / "audio.mp3"
        audio.touch()

        fake_result = Mock(returncode=0, stdout=json.dumps({"format": {"duration": "3.25"}}))
        with patch("core.domain.video_synthesis.subprocess.run", return_value=fake_result) as mock_run:
            duration = SlideVideoSegment._get_audio_duration(audio)

        assert duration == 3.25
        mock_run.assert_called_once()

    def test_from_files_uses_duration_extraction(self, tmp_path):
        """Factory should create a segment using extracted duration."""
        image = tmp_path / "slide_2.png"
        audio = tmp_path / "slide_2.mp3"
        image.touch()
        audio.touch()

        with patch.object(SlideVideoSegment, "_get_audio_duration", return_value=2.5):
            segment = SlideVideoSegment.from_files(2, image, audio)

        assert segment.duration_seconds == 2.5


class TestVideoSynthesisRequest:
    """Tests for synthesis request validation."""

    def test_request_validates_and_creates_segments(self, tmp_path):
        """Valid requests should normalize input paths and create segments."""
        image = tmp_path / "slide_1.png"
        audio = tmp_path / "slide_1.mp3"
        image.touch()
        audio.touch()
        request = VideoSynthesisRequest(
            slide_images=[str(image)],
            audio_files=[str(audio)],
            output_path=tmp_path / "output.mp4",
            config=VideoConfig(),
            presentation_id="deck",
        )

        with patch.object(VideoSynthesisRequest, "_extract_slide_number_from_files", return_value=1), patch.object(
            SlideVideoSegment,
            "from_files",
            return_value=Mock(validate_formats=Mock()),
        ) as mock_from_files:
            segments = request.create_segments()

        assert request.output_path == tmp_path / "output.mp4"
        assert request.slide_images == [image]
        assert request.audio_files == [audio]
        assert len(segments) == 1
        mock_from_files.assert_called_once()

    @pytest.mark.parametrize(
        "kwargs, message",
        [
            ({"slide_images": [], "audio_files": [Path("a.mp3")], "presentation_id": "deck"}, "At least one slide image"),
            ({"slide_images": [Path("a.png")], "audio_files": [], "presentation_id": "deck"}, "At least one audio file"),
            ({"slide_images": [Path("a.png")], "audio_files": [Path("b.mp3")], "presentation_id": ""}, "Presentation ID is required"),
        ],
    )
    def test_request_rejects_invalid_shapes(self, kwargs, message):
        """Invalid requests should be rejected."""
        kwargs.setdefault("output_path", Path("out.mp4"))
        kwargs.setdefault("config", VideoConfig())
        with pytest.raises(ValueError, match=message):
            VideoSynthesisRequest(**kwargs)

    def test_extract_slide_number_from_files_checks_matching_numbers(self, tmp_path):
        """Slide numbers should match between paired image/audio names."""
        image = tmp_path / "slide_3_reimagined.png"
        audio = tmp_path / "slide_3_hash.mp3"
        image.touch()
        audio.touch()
        request = VideoSynthesisRequest(
            slide_images=[image],
            audio_files=[audio],
            output_path=tmp_path / "out.mp4",
            config=VideoConfig(),
            presentation_id="deck",
        )

        assert request._extract_slide_number_from_files(image, audio) == 3


class TestVideoSynthesisResult:
    """Tests for synthesis result helpers."""

    def test_success_and_failure_factories(self, tmp_path):
        """Factory helpers should build consistent success and failure results."""
        success = VideoSynthesisResult.success_result(
            output_path=tmp_path / "out.mp4",
            duration_seconds=12.5,
            file_size_bytes=2048,
            processing_time_seconds=3.0,
            slides_processed=5,
        )
        failure = VideoSynthesisResult.failure_result("boom")

        assert success.success is True
        assert failure.success is False
        assert success.get_file_size_mb() > 0
        assert success.get_processing_rate() > 0

    def test_post_init_validates_required_fields(self, tmp_path):
        """Result validation should enforce consistency."""
        with pytest.raises(ValueError, match="Successful result must have output path"):
            VideoSynthesisResult(True, None, 0.0, 0, 1.0)

        with pytest.raises(ValueError, match="Failed result must have error message"):
            VideoSynthesisResult(False, None, 0.0, 0, 1.0)


class TestVideoSynthesisErrors:
    """Tests for domain exception hierarchy."""

    def test_error_hierarchy(self):
        """Specialized errors should inherit from the base synthesis error."""
        assert issubclass(VideoConfigurationError, VideoSynthesisError)
        assert issubclass(VideoProcessingError, VideoSynthesisError)
        assert issubclass(AudioAnalysisError, VideoSynthesisError)
        assert issubclass(FileValidationError, VideoSynthesisError)
