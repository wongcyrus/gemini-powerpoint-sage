"""Tests for pure video service helpers."""

from services.video_service_helpers import (
    build_video_agent_prompt,
    build_video_prompt,
    extract_artifact_id,
    format_video_prompt_file,
)


class TestVideoServiceHelpers:
    """Tests for video helper functions."""

    def test_build_video_prompt_handles_empty_and_long_notes(self):
        """Prompt construction should be concise and bounded."""
        assert build_video_prompt("") == "Create an engaging visual representation of key concepts."

        prompt = build_video_prompt("This is a very long note " * 20)
        assert prompt.startswith("Create a professional 8-10 second video")
        assert len(prompt) < 400

    def test_build_video_agent_prompt_includes_notes_and_prompt(self):
        """Agent prompts should embed both the prompt and the speaker notes."""
        prompt = build_video_agent_prompt("Prompt text", "Speaker notes")

        assert "Prompt text" in prompt
        assert "Speaker notes" in prompt
        assert "8-10 second video" in prompt

    def test_extract_artifact_id_supports_multiple_patterns(self):
        """Artifact parsing should handle ids and video filenames."""
        assert extract_artifact_id('artifact_id: "video_123"') == "video_123"
        assert extract_artifact_id("result video_alpha.mp4") == "video_alpha.mp4"
        assert extract_artifact_id("generated video_beta") == "video_beta"
        assert extract_artifact_id("") == ""

    def test_format_video_prompt_file_renders_expected_sections(self):
        """Prompt-file formatting should preserve the key sections."""
        content = format_video_prompt_file(2, "Prompt", "Notes", "video_123")

        assert "Slide 2 Video Prompt" in content
        assert "Prompt:\nPrompt" in content
        assert "Speaker Notes:\nNotes" in content
        assert "Generated Video: video_123" in content
