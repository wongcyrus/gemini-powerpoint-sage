"""Pure helpers for video synthesis integration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

from config.config import Config
from core.domain.presentation import Presentation
from core.domain.video_synthesis import VideoConfig, VideoSynthesisRequest


def resolve_video_synthesis_inputs(
    config: Config,
    slide_images_dir: Path | None = None,
    audio_files_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Resolve the default input directories used by video synthesis."""
    return (
        Path(slide_images_dir or config.visuals_dir),
        Path(audio_files_dir or config.speech_dir),
    )


def build_video_synthesis_request(
    presentation: Presentation,
    slide_images: Iterable[Path],
    audio_files: Iterable[Path],
    output_path: Path,
    config: VideoConfig,
) -> VideoSynthesisRequest:
    """Build a synthesis request from the resolved inputs."""
    return VideoSynthesisRequest(
        slide_images=list(slide_images),
        audio_files=list(audio_files),
        output_path=output_path,
        config=config,
        presentation_id=presentation.pptx_path.stem,
    )


def build_video_output_path(
    config: Config,
    presentation: Presentation,
    custom_filename: str | None = None,
) -> Path:
    """Build the output path for a synthesized presentation video."""
    output_dir = Path(config.video_synthesis_dir)
    filename = custom_filename or f"{presentation.pptx_path.stem}_{presentation.language}_video.mp4"
    return output_dir / filename
