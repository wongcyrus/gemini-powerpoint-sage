"""Tests for video synthesis service helpers."""

from services.video_synthesis.video_synthesis_service_helpers import extract_slide_number_from_filenames


class TestVideoSynthesisServiceHelpers:
    """Tests for helper functions used by the video synthesis service."""

    def test_extract_slide_number_from_filenames(self):
        """Matching filenames should return the slide number."""
        assert extract_slide_number_from_filenames("slide_12_image.png", "slide_12_audio.mp3") == 12

    def test_extract_slide_number_from_filenames_rejects_missing_slide(self):
        """Missing slide numbers should raise a clear error."""
        try:
            extract_slide_number_from_filenames("image.png", "slide_12_audio.mp3")
        except ValueError as exc:
            assert "image filename" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Expected ValueError")

    def test_extract_slide_number_from_filenames_rejects_missing_audio_slide(self):
        """Missing audio slide numbers should raise a clear error."""
        try:
            extract_slide_number_from_filenames("slide_12_image.png", "audio.mp3")
        except ValueError as exc:
            assert "audio filename" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Expected ValueError")

    def test_extract_slide_number_from_filenames_rejects_mismatch(self):
        """Mismatched slide numbers should raise a clear error."""
        try:
            extract_slide_number_from_filenames("slide_1.png", "slide_2.mp3")
        except ValueError as exc:
            assert "Slide number mismatch" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Expected ValueError")
