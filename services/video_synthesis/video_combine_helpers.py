"""Pure helpers for video combination preparation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from core.domain.video_synthesis import FileValidationError, VideoProcessingError


def validate_video_paths(video_paths: Iterable[Path]) -> None:
    """Ensure every input video exists and is a file."""
    for video_path in video_paths:
        if not video_path.exists():
            raise FileValidationError(f"Video file not found: {video_path}")
        if not video_path.is_file():
            raise FileValidationError(f"Path is not a file: {video_path}")


def calculate_total_video_duration(
    video_paths: Iterable[Path],
    timeout: int = 10,
) -> float:
    """Probe each video and sum its duration."""
    total_duration = 0.0
    for video_path in video_paths:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise VideoProcessingError(f"Failed to get duration for {video_path}")
        try:
            total_duration += float(result.stdout.strip())
        except ValueError as exc:
            raise VideoProcessingError(f"Failed to analyze video {video_path}: {exc}") from exc
    return total_duration


def build_concat_command(concat_file: Path, output_path: Path) -> list[str]:
    """Build the FFmpeg concat command."""
    return [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(output_path),
    ]
