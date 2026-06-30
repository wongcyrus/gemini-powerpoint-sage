"""Tests for presentation processor phase methods."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from services.presentation_processor import PresentationProcessor


def _make_phase_processor():
    processor = PresentationProcessor.__new__(PresentationProcessor)
    processor.config = SimpleNamespace(
        language="en",
        pptx_path="/tmp/demo.pptx",
        visual_style="professional",
        visuals_dir="/tmp/visuals",
        output_path="/tmp/notes.pptx",
        output_path_with_visuals="/tmp/visuals.pptx",
        generate_videos=False,
        retry_errors=False,
        speaker_style="professional",
        _get_output_dir=lambda: "/tmp/out",
        get_presentation_theme=lambda: "Theme",
    )
    processor.retry_errors = False
    processor.progress_file = "/tmp/progress.json"
    processor.tts_orchestrator = Mock()
    processor.tts_orchestrator.get_orchestrator_stats.return_value = {
        "cache": {"total_entries": 3, "total_size_mb": 1.2}
    }
    processor.visual_generator = Mock()
    processor.image_translator_agent = None
    processor.translator_agent = None
    processor.video_service = None
    processor.supervisor_agent = SimpleNamespace(tools=[])
    processor.tool_factory = Mock()
    processor.tool_factory.create_analyst_tool.return_value = "analyst"
    processor.tool_factory.create_writer_tool.return_value = "writer"
    processor.tool_factory.create_auditor_tool.return_value = "auditor"
    processor.tool_factory.create_translator_tool.return_value = "translator"
    return processor


class TestPresentationProcessorPhases:
    """Tests for the heavier orchestration phases."""

    def test_phase_generate_tts_updates_progress(self, monkeypatch):
        processor = _make_phase_processor()
        progress = {"slides": {"slide_1_hash": {"slide_index": 1}, "slide_2_hash": {"slide_index": 2}}}
        slide_data = [
            {"slide_idx": 1, "speaker_notes": "Note 1", "status": "success"},
            {"slide_idx": 2, "speaker_notes": "", "status": "failed"},
        ]

        tts_result = SimpleNamespace(
            is_valid=lambda: True,
            file_path="/tmp/audio1.mp3",
            engine_used=SimpleNamespace(value="gemini"),
            duration_seconds=1.5,
            cache_key="cache-1",
            style_prompt="style",
            metadata={},
        )

        processor.tts_orchestrator.process_single_language_batch = AsyncMock(return_value=[tts_result])
        save_progress = Mock()
        monkeypatch.setattr("services.presentation_processor.save_progress", save_progress)

        import asyncio

        asyncio.run(processor._phase_generate_tts(slide_data, progress))

        assert progress["slides"]["slide_1_hash"]["audio_file_path"] == "/tmp/audio1.mp3"
        assert progress["slides"]["slide_1_hash"]["tts_metadata"]["cache_key"] == "cache-1"
        save_progress.assert_called_once()
        processor.tts_orchestrator.get_orchestrator_stats.assert_called_once()

    def test_phase_generate_notes_happy_path(self, monkeypatch):
        processor = _make_phase_processor()
        slide_notes = Mock()
        slide_visuals = Mock()
        slide_notes_list = [slide_notes]
        slide_visuals_list = [slide_visuals]
        pdf_doc = [Mock()]
        progress = {"slides": {}}

        processor._extract_slide_image = Mock(return_value=SimpleNamespace())
        processor._process_slide_notes = AsyncMock(return_value=("final response", "success"))

        monkeypatch.setattr("services.presentation_processor.rotate_project", lambda: None)
        monkeypatch.setattr("services.presentation_processor.register_image", Mock())
        monkeypatch.setattr("services.presentation_processor.unregister_image", Mock())
        monkeypatch.setattr("utils.pptx_utils.get_slide_notes", lambda slide: "existing notes")
        monkeypatch.setattr("utils.pptx_utils.update_slide_notes", lambda slide, notes: setattr(slide, "updated_notes", notes))
        monkeypatch.setattr("services.presentation_processor.create_slide_key", lambda idx, notes: "slide_1_hash")
        save_progress = Mock()
        monkeypatch.setattr("services.presentation_processor.save_progress", save_progress)

        import asyncio

        slide_data = asyncio.run(
            processor._phase_generate_notes(
                prs_notes=SimpleNamespace(slides=slide_notes_list),
                prs_visuals=SimpleNamespace(slides=slide_visuals_list),
                pdf_doc=pdf_doc,
                limit=1,
                progress=progress,
                supervisor_runner=SimpleNamespace(),
                presentation_theme="Theme",
                global_context="Context",
            )
        )

        assert slide_data == [
            {
                "slide_idx": 1,
                "slide_visuals": slide_visuals,
                "slide_image": processor._extract_slide_image.return_value,
                "speaker_notes": "final response",
                "status": "success",
            }
        ]
        assert slide_notes.updated_notes == "final response"
        assert slide_visuals.updated_notes == "final response"
        save_progress.assert_called_once()

    def test_phase_generate_visuals_uses_existing_visual_generation(self, monkeypatch):
        processor = _make_phase_processor()
        slide_visual = Mock()
        slide_image = Mock()
        slide_data = [
            {
                "slide_idx": 1,
                "slide_visuals": slide_visual,
                "slide_image": slide_image,
                "speaker_notes": "Notes",
                "status": "success",
            }
        ]

        processor.visual_generator.generate_visual = AsyncMock(return_value=b"image-bytes")
        processor.visual_generator.replace_slide_with_visual.return_value = True
        monkeypatch.setattr("services.presentation_processor.rotate_project", lambda: None)

        import asyncio

        missing = asyncio.run(processor._phase_generate_visuals(Mock(), slide_data))

        assert missing == 0
        processor.visual_generator.generate_visual.assert_awaited_once()
        processor.visual_generator.replace_slide_with_visual.assert_called_once()

    def test_phase_generate_visuals_translates_existing_english_visual(self, tmp_path, monkeypatch):
        processor = _make_phase_processor()
        processor.config.language = "zh-CN"
        processor.config._get_output_dir = lambda: str(tmp_path)
        processor.config.pptx_path = str(tmp_path / "demo.pptx")
        processor.config.visuals_dir = str(tmp_path / "demo_zh-CN_visuals")
        processor.image_translator_agent = object()
        processor.visual_generator.generate_visual = AsyncMock()
        processor.visual_generator.replace_slide_with_visual.return_value = True

        english_dir = tmp_path / "demo_en_visuals"
        english_dir.mkdir(parents=True)
        english_image = english_dir / "slide_1_reimagined.png"
        from PIL import Image

        Image.new("RGB", (64, 64), color="white").save(english_image)

        slide_visual = Mock()
        slide_image = Mock()
        slide_data = [
            {
                "slide_idx": 1,
                "slide_visuals": slide_visual,
                "slide_image": slide_image,
                "speaker_notes": "Notes",
                "status": "success",
            }
        ]

        import asyncio

        with patch("services.presentation_processor.run_visual_agent", new=AsyncMock(return_value=b"translated-bytes")):
            missing = asyncio.run(processor._phase_generate_visuals(Mock(), slide_data))

        assert missing == 0
        processor.visual_generator.generate_visual.assert_not_awaited()
        processor.visual_generator.replace_slide_with_visual.assert_called_once()

    def test_phase_generate_visuals_skips_failed_notes(self, monkeypatch):
        processor = _make_phase_processor()
        slide_data = [
            {
                "slide_idx": 1,
                "slide_visuals": Mock(),
                "slide_image": Mock(),
                "speaker_notes": "Notes",
                "status": "failed",
            }
        ]

        processor.visual_generator.generate_visual = AsyncMock()
        monkeypatch.setattr("services.presentation_processor.rotate_project", lambda: None)

        import asyncio

        missing = asyncio.run(processor._phase_generate_visuals(Mock(), slide_data))

        assert missing == 1
        processor.visual_generator.generate_visual.assert_not_awaited()

    def test_process_aborts_when_visuals_fail(self, monkeypatch):
        processor = _make_phase_processor()
        processor.config.pdf_path = "/tmp/demo.pdf"
        processor.config.pptx_path = "/tmp/demo.pptx"
        processor.config.language = "yue-HK"
        processor._phase_generate_notes = AsyncMock(return_value=[])
        processor._phase_generate_tts = AsyncMock()
        processor._phase_generate_visuals = AsyncMock(return_value=1)
        processor._phase_generate_videos = AsyncMock()
        processor._save_outputs = Mock()
        processor._get_global_context = AsyncMock(return_value="context")
        processor._configure_supervisor_tools = Mock()
        processor._initialize_supervisor = AsyncMock(return_value=SimpleNamespace())
        processor.config.get_presentation_theme = lambda: "Theme"
        monkeypatch.setattr(
            "services.presentation_processor.Presentation",
            lambda *_args, **_kwargs: SimpleNamespace(slides=[Mock()])
        )
        monkeypatch.setattr(
            "services.presentation_processor.pymupdf.open",
            lambda *_args, **_kwargs: [Mock()]
        )
        monkeypatch.setattr(
            "services.presentation_processor.load_progress",
            lambda *_args, **_kwargs: {"slides": {}}
        )

        import asyncio
        import pytest

        with pytest.raises(RuntimeError, match="failed to generate"):
            asyncio.run(processor.process())

        processor._phase_generate_videos.assert_not_awaited()
        processor._save_outputs.assert_not_called()

    def test_phase_generate_videos_generates_clips_and_updates_plan(self):
        processor = _make_phase_processor()
        processor.config.generate_videos = True
        processor.video_service = Mock()
        processor.video_service.plan_video_moments = AsyncMock(
            return_value={
                "should_generate": True,
                "moments": [
                    {
                        "slide_idx": 1,
                        "role": "intro",
                        "reason": "Opening hook.",
                        "prompt": "Opening concept",
                    }
                ],
                "source": "ai",
            }
        )
        processor.video_service.save_video_plan = AsyncMock(return_value="/tmp/out/video_plan.json")
        processor.video_service.generate_planned_videos = AsyncMock(
            return_value={
                "should_generate": True,
                "moments": [
                    {
                        "slide_idx": 1,
                        "role": "intro",
                        "reason": "Opening hook.",
                        "prompt": "Opening concept",
                        "status": "success",
                        "video_path": "/tmp/out/slide_1_intro_veo.mp4",
                    }
                ],
                "source": "ai",
                "generated_count": 1,
                "failed_count": 0,
            }
        )

        slide_data = [
            {"slide_idx": 1, "speaker_notes": "Intro", "status": "success"},
            {"slide_idx": 2, "speaker_notes": "Body", "status": "success"},
        ]

        import asyncio

        asyncio.run(processor._generate_videos_for_slides(slide_data, "Theme", "Global"))

        processor.video_service.plan_video_moments.assert_awaited_once()
        processor.video_service.generate_planned_videos.assert_awaited_once()
        assert processor.video_service.save_video_plan.await_count == 2
