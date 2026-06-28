"""Tests for video configuration manager."""

from core.domain.video_synthesis import VideoConfig, VideoConfigurationError
from services.video_synthesis.video_config_manager import VideoConfigManager


class TestVideoConfigManager:
    """Tests for VideoConfigManager."""

    def test_creates_expected_presets(self):
        """Preset builders should return the expected shapes."""
        manager = VideoConfigManager()

        default = manager.create_default_config()
        hd = manager.create_hd_config()
        ultra = manager.create_4k_config()
        web = manager.create_web_optimized_config()

        assert default.resolution == (1920, 1080)
        assert hd.resolution == (1280, 720)
        assert ultra.resolution == (3840, 2160)
        assert web.fade_duration == 0.3
        assert manager.default_config == default

    def test_validate_config_accepts_valid_input(self):
        """Valid configs should pass validation."""
        manager = VideoConfigManager()
        manager.validate_config(VideoConfig())

    def test_validate_config_rejects_bad_resolution(self):
        """Bad resolution should raise a domain error."""
        manager = VideoConfigManager()

        config = VideoConfig(resolution=(0, 720))
        try:
            manager.validate_config(config)
        except VideoConfigurationError as exc:
            assert "Invalid resolution" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Expected VideoConfigurationError")

    def test_validate_config_rejects_bad_fps_and_audio_codec(self):
        """Invalid fps and audio codec values should be rejected."""
        manager = VideoConfigManager()

        bad_fps = VideoConfig(fps=0)
        bad_audio = VideoConfig(audio_codec="ogg")

        for config in (bad_fps, bad_audio):
            try:
                manager.validate_config(config)
            except VideoConfigurationError as exc:
                assert "Invalid FPS" in str(exc) or "Unsupported audio codec" in str(exc)
            else:  # pragma: no cover
                raise AssertionError("Expected VideoConfigurationError")

    def test_validate_config_rejects_bad_codec_combination(self):
        """Unsupported codec combinations should be rejected."""
        manager = VideoConfigManager()

        config = VideoConfig(video_codec="libvpx", audio_codec="aac", output_format="webm")
        try:
            manager.validate_config(config)
        except VideoConfigurationError as exc:
            assert "not compatible" in str(exc).lower() or "unsupported" in str(exc).lower()
        else:  # pragma: no cover
            raise AssertionError("Expected VideoConfigurationError")

    def test_validate_bitrate_rejects_bad_format(self):
        """Malformed bitrate strings should fail validation."""
        manager = VideoConfigManager()

        try:
            manager._validate_bitrate("not-a-bitrate", "video")
        except VideoConfigurationError as exc:
            assert "Invalid video bitrate format" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Expected VideoConfigurationError")

    def test_validate_bitrate_formats(self):
        """Bitrate helper should accept common styles."""
        manager = VideoConfigManager()
        manager._validate_bitrate("2M", "video")
        manager._validate_bitrate("128k", "audio")
        manager._validate_bitrate("500000", "audio")

    def test_validate_bitrate_rejects_invalid(self):
        """Bitrate helper should reject malformed values."""
        manager = VideoConfigManager()

        for value in ("0", "-1k", "abc"):
            try:
                manager._validate_bitrate(value, "video")
            except VideoConfigurationError:
                pass
            else:  # pragma: no cover
                raise AssertionError(f"Expected failure for {value}")

    def test_validate_config_rejects_invalid_codec_format_and_fade(self):
        """Invalid codec, format, and fade settings should fail validation."""
        manager = VideoConfigManager()

        bad_codec = VideoConfig(video_codec="bad", audio_codec="aac")
        bad_format = VideoConfig(output_format="flv")
        bad_fade = VideoConfig(fade_duration=-0.1)

        for config in (bad_codec, bad_format, bad_fade):
            try:
                manager.validate_config(config)
            except VideoConfigurationError:
                pass
            else:  # pragma: no cover
                raise AssertionError("Expected VideoConfigurationError")

    def test_validate_config_accepts_unusual_but_valid_values(self):
        """Unusual values that are still valid should not raise."""
        manager = VideoConfigManager()
        config = VideoConfig(resolution=(1000, 700), fps=240, fade_duration=6.0)

        manager.validate_config(config)

    def test_create_config_from_dict_and_summary(self):
        """Config dictionaries should normalize and summarize cleanly."""
        manager = VideoConfigManager()

        config = manager.create_config_from_dict({"resolution": [1280, 720], "fade_duration": 0.2})
        summary = manager.get_config_summary(config)

        assert config.resolution == (1280, 720)
        assert summary["resolution"] == "1280x720"
        assert summary["quality_level"] == "HD"

    def test_create_config_from_dict_rejects_unknown_key(self):
        """Unexpected config keys should raise a configuration error."""
        manager = VideoConfigManager()

        try:
            manager.create_config_from_dict({"unknown_key": True})
        except VideoConfigurationError as exc:
            assert "Invalid configuration parameters" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Expected VideoConfigurationError")

    def test_create_config_from_dict_rejects_bad_resolution(self):
        """Resolution lists must have exactly two elements."""
        manager = VideoConfigManager()

        try:
            manager.create_config_from_dict({"resolution": [1280]})
        except VideoConfigurationError as exc:
            assert "Invalid resolution format" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("Expected VideoConfigurationError")

    def test_get_config_summary_and_optimize_for_content_cover_edge_cases(self):
        """Summaries and optimization should handle 4K and empty-slide scenarios."""
        manager = VideoConfigManager()
        config = manager.create_4k_config()

        summary = manager.get_config_summary(config)
        assert summary["quality_level"] == "4K/Ultra HD"
        assert summary["output_format"] == "MP4"

        optimized = manager.optimize_config_for_content(config, total_duration=5000, slide_count=0)
        assert optimized.fade_duration == config.fade_duration

    def test_get_config_summary_reports_standard_definition(self):
        """Small resolutions should be summarized as standard definition."""
        manager = VideoConfigManager()
        config = VideoConfig(resolution=(640, 360))

        summary = manager.get_config_summary(config)

        assert summary["quality_level"] == "Standard Definition"
        assert summary["resolution"] == "640x360"

    def test_optimize_config_for_content(self):
        """Short content should reduce fade duration."""
        manager = VideoConfigManager()
        base = manager.create_default_config()

        optimized = manager.optimize_config_for_content(base, total_duration=12, slide_count=4)

        assert optimized.fade_duration <= base.fade_duration

    def test_optimize_config_for_content_keeps_fade_for_long_segments(self):
        """Long slide durations should preserve the configured fade duration."""
        manager = VideoConfigManager()
        base = manager.create_default_config()

        optimized = manager.optimize_config_for_content(base, total_duration=100, slide_count=10)

        assert optimized.fade_duration == base.fade_duration
