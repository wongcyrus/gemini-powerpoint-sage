"""Tests for pure presentation processor helper functions."""

from services.presentation_processor_helpers import (
    build_global_context_translation_prompt,
    build_visual_translation_prompt,
    build_supervisor_prompt,
    extract_artifact_id,
    extract_video_prompt,
    get_language_name,
    is_error_response,
)


class TestPresentationProcessorHelpersModule:
    """Tests for the extracted pure helper functions."""

    def test_is_error_response_matches_only_specific_patterns(self):
        """Error detection should remain narrowly scoped."""
        assert is_error_response("system_error: boom") is True
        assert is_error_response("Failed: tool blew up") is True
        assert is_error_response("This is a normal response.") is False

    def test_build_supervisor_prompt_includes_context_and_language(self):
        """Prompt construction should keep the same formatted context."""
        prompt = build_supervisor_prompt(
            slide_idx=3,
            image_id="img-3",
            existing_notes="Existing",
            previous_slide_summary="Previous summary",
            presentation_theme="Cyberpunk",
            global_context="Global context",
            target_language="zh-CN",
            total_slides=5,
            previous_speaker_notes=[{"slide_idx": 1, "notes": "One"}, {"slide_idx": 2, "notes": "Two"}],
        )

        assert "MIDDLE slide" in prompt
        assert "TARGET_LANGUAGE: zh-CN" in prompt
        assert "PREVIOUS_SPEAKER_NOTES" in prompt
        assert "Slide 2: Two" in prompt

    def test_build_supervisor_prompt_marks_first_and_last_slide(self):
        """First and last slide prompts should carry their special instructions."""
        first = build_supervisor_prompt(
            slide_idx=1,
            image_id="img-1",
            existing_notes="Existing",
            previous_slide_summary="Previous summary",
            presentation_theme="Cyberpunk",
            global_context="Global context",
            target_language="en",
            total_slides=3,
        )
        last = build_supervisor_prompt(
            slide_idx=3,
            image_id="img-3",
            existing_notes="Existing",
            previous_slide_summary="Previous summary",
            presentation_theme="Cyberpunk",
            global_context="Global context",
            target_language="en",
            total_slides=3,
        )

        assert "FIRST slide" in first
        assert "LAST slide" in last

    def test_extract_video_prompt_handles_empty_and_long_notes(self):
        """Video prompts should be concise and have a fallback."""
        assert extract_video_prompt("") == "Create an engaging visual representation of key concepts."

        prompt = extract_video_prompt("This is a very long note " * 20)
        assert prompt.startswith("Create a professional 8-10 second video")
        assert len(prompt) < 400

    def test_extract_artifact_id_finds_multiple_response_shapes(self):
        """Artifact parsing should support IDs and video file references."""
        assert extract_artifact_id('artifact_id="video_123"') == "video_123"
        assert extract_artifact_id("generated video_abc.mp4") == "video_abc.mp4"
        assert extract_artifact_id("generated video_clip") == "video_clip"
        assert extract_artifact_id("") == ""

    def test_get_language_name_falls_back_to_locale(self):
        """Known locales should map to display names and unknown ones should pass through."""
        assert get_language_name("zh-CN") == "Simplified Chinese (简体中文)"
        assert get_language_name("xx-YY") == "xx-YY"

    def test_build_global_context_translation_prompt_includes_locale_rules(self):
        """Global context translation prompts should include Chinese locale instructions."""
        prompt = build_global_context_translation_prompt(
            "Overview",
            "Simplified Chinese (简体中文)",
            "zh-CN",
        )

        assert "Translate the following presentation overview" in prompt
        assert "Simplified Chinese (简体中文)" in prompt
        assert "ONLY Simplified Chinese characters" in prompt

    def test_build_global_context_translation_prompt_handles_traditional_chinese(self):
        """Traditional Chinese locales should get the right locale instruction."""
        prompt = build_global_context_translation_prompt(
            "Overview",
            "Traditional Chinese (繁體中文)",
            "zh-TW",
        )

        assert "ONLY Traditional Chinese characters" in prompt

    def test_build_visual_translation_prompt_includes_layout_constraints(self):
        """Visual translation prompts should preserve layout constraints."""
        prompt = build_visual_translation_prompt("Japanese (日本語)", "Notes")

        assert "Translate this English slide visual" in prompt
        assert "Keep the exact same layout and structure" in prompt
        assert "Speaker Notes: Notes" in prompt
