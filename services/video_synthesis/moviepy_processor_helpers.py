"""Pure helpers for MoviePy video processing."""

from __future__ import annotations

from core.domain.video_synthesis import VideoConfig


def build_moviepy_cache_config(config: VideoConfig) -> dict:
    """Build the cache key inputs used for MoviePy segment reuse."""
    return {
        "resolution": config.resolution,
        "fps": config.fps,
        "video_codec": config.video_codec,
        "audio_codec": config.audio_codec,
        "video_bitrate": config.video_bitrate,
        "audio_bitrate": config.audio_bitrate,
        "output_format": config.output_format,
        "fade_duration": config.fade_duration,
    }


def calculate_segment_layout(
    img_width: int,
    img_height: int,
    target_resolution: tuple[int, int],
    max_dimension: int = 1920,
) -> dict:
    """Calculate pre-resize, final resize, and centering info for a segment."""
    target_width, target_height = target_resolution
    pre_width, pre_height = img_width, img_height

    if img_width > 2048 or img_height > 2048:
        if img_width > img_height:
            pre_width = max_dimension
            pre_height = int(img_height * max_dimension / img_width)
        else:
            pre_height = max_dimension
            pre_width = int(img_width * max_dimension / img_height)

    scale_width = target_width / pre_width
    scale_height = target_height / pre_height
    scale = min(scale_width, scale_height)

    final_width = int(pre_width * scale)
    final_height = int(pre_height * scale)

    return {
        "pre_size": (pre_width, pre_height),
        "final_size": (final_width, final_height),
        "needs_background": final_width != target_width or final_height != target_height,
        "offset": (
            (target_width - final_width) // 2,
            (target_height - final_height) // 2,
        ),
    }
