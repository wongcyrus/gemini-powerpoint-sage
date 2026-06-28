"""Tests for video synthesis integration helpers."""

from pathlib import Path
from types import SimpleNamespace

from core.domain.video_synthesis import VideoConfig
from services.video_synthesis.integration_helpers import (
    build_video_output_path,
    build_video_synthesis_request,
    resolve_video_synthesis_inputs,
)


class TestVideoSynthesisIntegrationHelpers:
    """Tests for request and path builders."""

    def test_resolve_video_synthesis_inputs_uses_config_defaults(self):
        config = SimpleNamespace(visuals_dir="/tmp/visuals", speech_dir="/tmp/speech")

        slide_dir, audio_dir = resolve_video_synthesis_inputs(config)

        assert slide_dir == Path("/tmp/visuals")
        assert audio_dir == Path("/tmp/speech")

    def test_build_video_output_path_uses_presentation_language(self):
        config = SimpleNamespace(video_synthesis_dir="/tmp/videos")
        presentation = SimpleNamespace(pptx_path=Path("/tmp/demo.pptx"), language="en")

        output_path = build_video_output_path(config, presentation)

        assert output_path == Path("/tmp/videos/demo_en_video.mp4")

    def test_build_video_synthesis_request_preserves_inputs(self, tmp_path):
        config = VideoConfig()
        presentation = SimpleNamespace(pptx_path=tmp_path / "demo.pptx")
        slide_image = tmp_path / "slide1.png"
        audio_file = tmp_path / "slide1.mp3"
        output_path = tmp_path / "out.mp4"
        slide_image.write_bytes(b"img")
        audio_file.write_bytes(b"audio")
        presentation.pptx_path.write_text("pptx")

        request = build_video_synthesis_request(
            presentation=presentation,
            slide_images=[slide_image],
            audio_files=[audio_file],
            output_path=output_path,
            config=config,
        )

        assert request.slide_images == [slide_image]
        assert request.audio_files == [audio_file]
        assert request.output_path == output_path
        assert request.presentation_id == "demo"
