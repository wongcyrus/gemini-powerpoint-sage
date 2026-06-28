"""Tests for presentation processor TTS helpers."""

from services.presentation_processor_tts_helpers import build_tts_slide_data


class TestPresentationProcessorTTSHelpers:
    """Tests for TTS slide-data preparation."""

    def test_build_tts_slide_data_filters_successful_slides(self):
        """Only successful slides with notes should become TTS inputs."""
        slide_data = [
            {"slide_idx": 1, "status": "success", "speaker_notes": "One"},
            {"slide_idx": 2, "status": "failed", "speaker_notes": "Two"},
            {"slide_idx": 3, "status": "success", "speaker_notes": ""},
        ]

        tts_slides = build_tts_slide_data(slide_data, "zh-CN", "demo")

        assert len(tts_slides) == 1
        assert tts_slides[0].slide_number == 1
        assert tts_slides[0].language_code == "zh-CN"
        assert tts_slides[0].presentation_id == "demo"
        assert tts_slides[0].get_combined_text().startswith("Content: One")
