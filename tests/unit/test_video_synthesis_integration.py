"""Tests for video synthesis integration."""

from pathlib import Path
from types import SimpleNamespace

from core.domain.video_synthesis import VideoConfig
from services.video_synthesis.integration import VideoSynthesisIntegration


class TestVideoSynthesisIntegration:
    """Tests for video synthesis orchestration."""

    def test_is_video_synthesis_enabled_false_when_service_missing(self):
        config = SimpleNamespace(enable_video_synthesis=True)
        integration = VideoSynthesisIntegration.__new__(VideoSynthesisIntegration)
        integration.config = config
        integration.video_service = None

        assert integration.is_video_synthesis_enabled() is False

    def test_get_video_synthesis_status_when_disabled(self):
        integration = VideoSynthesisIntegration.__new__(VideoSynthesisIntegration)
        integration.config = SimpleNamespace(enable_video_synthesis=False, video_synthesis_dir="/tmp/videos")
        integration.video_service = None

        status = integration.get_video_synthesis_status()

        assert status["enabled"] is False
        assert status["service_available"] is False

    def test_is_video_synthesis_enabled_false_when_config_disabled(self):
        config = SimpleNamespace(enable_video_synthesis=False)
        integration = VideoSynthesisIntegration.__new__(VideoSynthesisIntegration)
        integration.config = config
        integration.video_service = None

        assert integration.is_video_synthesis_enabled() is False

    def test_create_video_from_presentation_builds_request_and_returns_result(self, monkeypatch, tmp_path):
        pptx_path = tmp_path / "demo.pptx"
        slide_image = tmp_path / "slide1.png"
        audio_file = tmp_path / "slide1.mp3"
        pptx_path.write_text("pptx")
        slide_image.write_bytes(b"img")
        audio_file.write_bytes(b"audio")

        config = SimpleNamespace(
            enable_video_synthesis=True,
            visuals_dir=str(tmp_path / "visuals"),
            speech_dir=str(tmp_path / "speech"),
            video_synthesis_dir=str(tmp_path / "videos"),
            get_video_synthesis_config=lambda: VideoConfig(
                resolution=(1280, 720),
                fps=30,
                video_codec="libx264",
                audio_codec="aac",
                video_bitrate="2M",
                audio_bitrate="192k",
                output_format="mp4",
                fade_duration=1.5,
            ),
        )
        monkeypatch.setattr(
            "services.video_synthesis.integration.FileService",
            lambda: SimpleNamespace(),
        )
        monkeypatch.setattr(
            "services.video_synthesis.integration.VideoSynthesisService",
            lambda temp_dir=None: SimpleNamespace(),
        )
        integration = VideoSynthesisIntegration(config)
        integration.video_service = SimpleNamespace(
            synthesize_video=lambda request: SimpleNamespace(
                success=True, output_path=Path("/tmp/rendered.mp4")
            )
        )

        monkeypatch.setattr(
            "services.video_synthesis.integration.resolve_video_synthesis_inputs",
            lambda cfg, slide_images_dir=None, audio_files_dir=None: (
                tmp_path / "visuals",
                tmp_path / "speech",
            ),
        )
        monkeypatch.setattr(
            integration,
            "_find_slide_images",
            lambda images_dir, expected_count: [slide_image],
        )
        monkeypatch.setattr(
            integration,
            "_find_audio_files",
            lambda audio_dir, expected_count: [audio_file],
        )

        presentation = SimpleNamespace(
            pptx_path=pptx_path,
            language="en",
            total_slides=lambda: 1,
            pptx_name="demo",
        )

        result = integration.create_video_from_presentation(presentation)

        assert result == Path("/tmp/rendered.mp4")

    def test_create_video_from_presentation_returns_none_when_disabled(self):
        integration = VideoSynthesisIntegration.__new__(VideoSynthesisIntegration)
        integration.config = SimpleNamespace(enable_video_synthesis=False)
        integration.video_service = None

        assert integration.create_video_from_presentation(SimpleNamespace(pptx_path=Path("/tmp/demo.pptx"))) is None

    def test_create_video_from_presentation_returns_none_when_no_files_found(self, monkeypatch, tmp_path):
        config = SimpleNamespace(
            enable_video_synthesis=True,
            visuals_dir=str(tmp_path / "visuals"),
            speech_dir=str(tmp_path / "speech"),
            video_synthesis_dir=str(tmp_path / "videos"),
            get_video_synthesis_config=lambda: VideoConfig(
                resolution=(1280, 720),
                fps=30,
                video_codec="libx264",
                audio_codec="aac",
                video_bitrate="2M",
                audio_bitrate="192k",
                output_format="mp4",
                fade_duration=1.5,
            ),
        )
        monkeypatch.setattr("services.video_synthesis.integration.FileService", lambda: SimpleNamespace())
        monkeypatch.setattr("services.video_synthesis.integration.VideoSynthesisService", lambda temp_dir=None: SimpleNamespace())
        integration = VideoSynthesisIntegration(config)
        monkeypatch.setattr(
            "services.video_synthesis.integration.resolve_video_synthesis_inputs",
            lambda cfg, slide_images_dir=None, audio_files_dir=None: (Path(config.visuals_dir), Path(config.speech_dir)),
        )
        monkeypatch.setattr(integration, "_find_slide_images", lambda images_dir, expected_count: [])
        monkeypatch.setattr(integration, "_find_audio_files", lambda audio_dir, expected_count: [])

        presentation = SimpleNamespace(pptx_path=tmp_path / "demo.pptx", total_slides=lambda: 1)

        assert integration.create_video_from_presentation(presentation) is None

    def test_create_video_from_presentation_returns_none_when_config_missing(self, monkeypatch, tmp_path):
        config = SimpleNamespace(
            enable_video_synthesis=True,
            visuals_dir=str(tmp_path / "visuals"),
            speech_dir=str(tmp_path / "speech"),
            video_synthesis_dir=str(tmp_path / "videos"),
            get_video_synthesis_config=lambda: None,
        )
        monkeypatch.setattr("services.video_synthesis.integration.FileService", lambda: SimpleNamespace())
        monkeypatch.setattr("services.video_synthesis.integration.VideoSynthesisService", lambda temp_dir=None: SimpleNamespace())
        integration = VideoSynthesisIntegration(config)
        integration.video_service = SimpleNamespace()
        monkeypatch.setattr(
            "services.video_synthesis.integration.resolve_video_synthesis_inputs",
            lambda cfg, slide_images_dir=None, audio_files_dir=None: (Path(config.visuals_dir), Path(config.speech_dir)),
        )
        monkeypatch.setattr(integration, "_find_slide_images", lambda images_dir, expected_count: [tmp_path / "slide1.png"])
        monkeypatch.setattr(integration, "_find_audio_files", lambda audio_dir, expected_count: [tmp_path / "slide1.mp3"])

        presentation = SimpleNamespace(pptx_path=tmp_path / "demo.pptx", total_slides=lambda: 1)

        assert integration.create_video_from_presentation(presentation) is None

    def test_create_video_from_presentation_returns_none_on_mismatch(self, monkeypatch, tmp_path):
        config = SimpleNamespace(
            enable_video_synthesis=True,
            visuals_dir=str(tmp_path / "visuals"),
            speech_dir=str(tmp_path / "speech"),
            video_synthesis_dir=str(tmp_path / "videos"),
            get_video_synthesis_config=lambda: None,
        )
        monkeypatch.setattr(
            "services.video_synthesis.integration.FileService",
            lambda: SimpleNamespace(),
        )
        monkeypatch.setattr(
            "services.video_synthesis.integration.VideoSynthesisService",
            lambda temp_dir=None: SimpleNamespace(),
        )
        integration = VideoSynthesisIntegration(config)
        integration.video_service = SimpleNamespace()
        monkeypatch.setattr(
            "services.video_synthesis.integration.resolve_video_synthesis_inputs",
            lambda cfg, slide_images_dir=None, audio_files_dir=None: (
                Path(config.visuals_dir),
                Path(config.speech_dir),
            ),
        )
        monkeypatch.setattr(
            integration,
            "_find_slide_images",
            lambda images_dir, expected_count: [tmp_path / "slide1.png"],
        )
        monkeypatch.setattr(
            integration,
            "_find_audio_files",
            lambda audio_dir, expected_count: [tmp_path / "slide1.mp3", tmp_path / "slide2.mp3"],
        )

        presentation = SimpleNamespace(
            pptx_path=tmp_path / "demo.pptx",
            language="en",
            total_slides=lambda: 2,
        )

        assert integration.create_video_from_presentation(presentation) is None

    def test_create_video_from_presentation_directories_uses_config_dirs(self, monkeypatch, tmp_path):
        config = SimpleNamespace(
            enable_video_synthesis=True,
            visuals_dir=str(tmp_path / "visuals"),
            speech_dir=str(tmp_path / "speech"),
            video_synthesis_dir=str(tmp_path / "videos"),
            get_video_synthesis_config=lambda: VideoConfig(
                resolution=(1280, 720),
                fps=30,
                video_codec="libx264",
                audio_codec="aac",
                video_bitrate="2M",
                audio_bitrate="192k",
                output_format="mp4",
                fade_duration=1.5,
            ),
        )
        monkeypatch.setattr(
            "services.video_synthesis.integration.FileService",
            lambda: SimpleNamespace(),
        )
        monkeypatch.setattr(
            "services.video_synthesis.integration.VideoSynthesisService",
            lambda temp_dir=None: SimpleNamespace(),
        )
        integration = VideoSynthesisIntegration(config)
        calls = []
        integration.create_video_from_presentation = lambda **kwargs: calls.append(kwargs) or Path("/tmp/out.mp4")

        presentation = SimpleNamespace(pptx_path=tmp_path / "demo.pptx", total_slides=lambda: 1)
        result = integration.create_video_from_presentation_directories(presentation, output_filename="custom.mp4")

        assert result == Path("/tmp/out.mp4")
        assert calls[0]["slide_images_dir"] == Path(config.visuals_dir)
        assert calls[0]["audio_files_dir"] == Path(config.speech_dir)

    def test_create_video_from_slide_audio_pairs_returns_none_when_disabled(self):
        integration = VideoSynthesisIntegration.__new__(VideoSynthesisIntegration)
        integration.config = SimpleNamespace(enable_video_synthesis=False)
        integration.video_service = None

        assert (
            integration.create_video_from_slide_audio_pairs(
                slide_audio_pairs=[],
                output_path=Path("/tmp/out.mp4"),
            )
            is None
        )

    def test_find_slide_images_and_audio_files_use_pattern_fallbacks(self, tmp_path):
        integration = VideoSynthesisIntegration.__new__(VideoSynthesisIntegration)
        integration.config = SimpleNamespace(enable_video_synthesis=True, video_synthesis_dir=str(tmp_path / "videos"))
        integration.video_service = None

        images_dir = tmp_path / "images"
        audio_dir = tmp_path / "audio"
        images_dir.mkdir()
        audio_dir.mkdir()
        (images_dir / "foo_slide_2.png").write_bytes(b"img")
        (images_dir / "foo_slide_1.png").write_bytes(b"img")
        (audio_dir / "speech_2.mp3").write_bytes(b"audio")
        (audio_dir / "speech_1.mp3").write_bytes(b"audio")

        images = integration._find_slide_images(images_dir, expected_count=1)
        audio = integration._find_audio_files(audio_dir, expected_count=1)

        assert images[0].name == "foo_slide_1.png"
        assert audio[0].name == "speech_1.mp3"

    def test_get_video_synthesis_status_includes_supported_formats(self, tmp_path):
        integration = VideoSynthesisIntegration.__new__(VideoSynthesisIntegration)
        integration.config = SimpleNamespace(enable_video_synthesis=True, video_synthesis_dir=str(tmp_path / "videos"))
        integration.video_service = SimpleNamespace(get_supported_formats=lambda: [".mp4", ".mov"])

        status = integration.get_video_synthesis_status()

        assert status["enabled"] is True
        assert status["service_available"] is True
        assert status["supported_formats"] == [".mp4", ".mov"]
