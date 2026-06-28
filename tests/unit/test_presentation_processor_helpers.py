"""Tests for pure PresentationProcessor helper methods."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from PIL import Image

from services.presentation_processor import PresentationProcessor


class TestPresentationProcessorHelpers:
    """Tests for small PresentationProcessor helper methods."""

    def _make_processor(self):
        processor = PresentationProcessor.__new__(PresentationProcessor)
        processor.config = SimpleNamespace(
            language="zh-CN",
            speaker_style="teacher",
            visuals_dir="/tmp/visuals",
            skip_visuals=False,
            visual_style="cyberpunk",
            pptx_path="/tmp/deck.pptx",
            pdf_path="/tmp/deck.pdf",
            output_dir="/tmp/out",
            course_id="course-1",
            region="global",
            generate_videos=True,
            retry_errors=False,
            _get_output_dir=lambda: "/tmp/out",
            get_presentation_theme=lambda: "Theme",
        )
        processor.tool_factory = Mock()
        processor.tool_factory.create_analyst_tool.return_value = "analyst"
        processor.tool_factory.create_writer_tool.return_value = "writer"
        processor.tool_factory.create_auditor_tool.return_value = "auditor"
        processor.tool_factory.create_translator_tool.return_value = "translator"
        processor.supervisor_agent = SimpleNamespace(tools=[])
        processor.translator_agent = None
        processor.image_translator_agent = None
        processor.video_generator_agent = None
        return processor

    def test_is_error_response_detects_only_specific_patterns(self):
        """Error detection should remain narrowly scoped."""
        processor = self._make_processor()

        assert processor._is_error_response("system_error: boom") is True
        assert processor._is_error_response("Tool execution failed during generation") is True
        assert processor._is_error_response("This is a normal response.") is False

    def test_build_supervisor_prompt_includes_position_language_and_history(self):
        """Prompt building should include slide position and previous notes context."""
        processor = self._make_processor()

        prompt = processor._build_supervisor_prompt(
            slide_idx=2,
            image_id="img-2",
            existing_notes="Existing",
            previous_slide_summary="Prev summary",
            presentation_theme="Cyberpunk",
            global_context="Global",
            total_slides=5,
            previous_speaker_notes=[{"slide_idx": 1, "notes": "One"}, {"slide_idx": 2, "notes": "Two"}],
        )

        assert "MIDDLE slide" in prompt
        assert "TARGET_LANGUAGE: zh-CN" in prompt
        assert "PREVIOUS_SPEAKER_NOTES" in prompt
        assert "Slide 2" in prompt

    def test_extract_video_prompt_truncates_and_handles_empty_notes(self):
        """Video prompts should stay concise and fall back for empty notes."""
        processor = self._make_processor()

        assert processor._extract_video_prompt(1, "") == "Create an engaging visual representation of key concepts."

        prompt = processor._extract_video_prompt(1, "This is a very long note " * 20)
        assert prompt.startswith("Create a professional 8-10 second video")
        assert len(prompt) < 400

    def test_extract_artifact_id_handles_multiple_response_shapes(self):
        """Artifact parsing should support explicit IDs and filename references."""
        processor = self._make_processor()

        assert processor._extract_artifact_id('artifact_id="video_123"') == "video_123"
        assert processor._extract_artifact_id("generated video_abc.mp4") == "video_abc.mp4"
        assert processor._extract_artifact_id("generated video_clip") == "video_clip"
        assert processor._extract_artifact_id("") == ""

    def test_configure_supervisor_tools_adds_translator_when_available(self):
        """Translator tool should be appended only when a translator agent exists."""
        processor = self._make_processor()
        processor.translator_agent = object()

        processor._configure_supervisor_tools("Theme", "Global", {"1": "note"})

        assert processor.supervisor_agent.tools == ["analyst", "writer", "auditor", "translator"]
        processor.tool_factory.create_writer_tool.assert_called_once()
        processor.tool_factory.create_translator_tool.assert_called_once()

    def test_extract_slide_image_returns_placeholder_on_failure(self):
        """Broken pixmaps should fall back to a neutral placeholder image."""
        processor = self._make_processor()

        class BrokenPage:
            def get_pixmap(self, dpi=150):
                raise RuntimeError("boom")

        image = processor._extract_slide_image(BrokenPage())

        assert isinstance(image, Image.Image)
        assert image.size == (800, 600)
