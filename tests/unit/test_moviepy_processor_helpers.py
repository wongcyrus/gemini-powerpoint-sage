"""Tests for MoviePy processor helpers."""

from types import SimpleNamespace

from services.video_synthesis.moviepy_processor_helpers import (
    build_moviepy_cache_config,
    calculate_segment_layout,
)


class TestMoviePyProcessorHelpers:
    """Tests for cache config extraction."""

    def test_build_moviepy_cache_config_captures_relevant_fields(self):
        config = SimpleNamespace(
            resolution=(1280, 720),
            fps=30,
            video_codec="libx264",
            audio_codec="aac",
            video_bitrate="2M",
            audio_bitrate="192k",
            output_format="mp4",
            fade_duration=1.5,
        )

        cache_config = build_moviepy_cache_config(config)

        assert cache_config == {
            "resolution": (1280, 720),
            "fps": 30,
            "video_codec": "libx264",
            "audio_codec": "aac",
            "video_bitrate": "2M",
            "audio_bitrate": "192k",
            "output_format": "mp4",
            "fade_duration": 1.5,
        }

    def test_calculate_segment_layout_scales_and_centers_large_images(self):
        layout = calculate_segment_layout(4000, 3000, (1280, 720))

        assert layout["pre_size"] == (1920, 1440)
        assert layout["final_size"] == (960, 720)
        assert layout["needs_background"] is True
        assert layout["offset"] == (160, 0)

    def test_calculate_segment_layout_scales_tall_large_images(self):
        layout = calculate_segment_layout(3000, 4000, (1280, 720))

        assert layout["pre_size"] == (1440, 1920)
        assert layout["final_size"] == (540, 720)
        assert layout["needs_background"] is True

    def test_calculate_segment_layout_keeps_exact_fit_without_background(self):
        layout = calculate_segment_layout(1280, 720, (1280, 720))

        assert layout["pre_size"] == (1280, 720)
        assert layout["final_size"] == (1280, 720)
        assert layout["needs_background"] is False
