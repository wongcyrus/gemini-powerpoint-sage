"""Pure helpers for video combination preparation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable
from core.domain.video_synthesis import VideoConfig

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


def build_normalized_concat_command(
    video_paths: Iterable[Path],
    output_path: Path,
    config: VideoConfig,
    audio_sample_rate: int = 48000,
    audio_channels: int = 2,
) -> list[str]:
    """Build an FFmpeg concat command that normalizes inputs before combining."""
    normalized_paths = [Path(path) for path in video_paths]
    if not normalized_paths:
        raise VideoProcessingError("No video files to concatenate")

    command = ["ffmpeg", "-y"]
    for video_path in normalized_paths:
        command.extend(["-i", str(video_path)])

    filter_parts: list[str] = []
    concat_inputs: list[str] = []
    width, height = config.resolution

    for index in range(len(normalized_paths)):
        filter_parts.append(
            f"[{index}:v:0]setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,fps={config.fps},format=yuv420p,setsar=1[v{index}]"
        )
        filter_parts.append(
            f"[{index}:a:0]asetpts=PTS-STARTPTS,aformat=sample_rates={audio_sample_rate}:channel_layouts=stereo[a{index}]"
        )
        concat_inputs.append(f"[v{index}][a{index}]")

    filter_complex = ";".join(filter_parts + [f"{''.join(concat_inputs)}concat=n={len(normalized_paths)}:v=1:a=1[v][a]"])
    command.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            config.video_codec,
            "-c:a",
            config.audio_codec,
            "-b:v",
            config.video_bitrate,
            "-b:a",
            config.audio_bitrate,
            "-ar",
            str(audio_sample_rate),
            "-ac",
            str(audio_channels),
        ]
    )

    if output_path.suffix.lower() == ".mp4":
        command.extend(["-movflags", "+faststart"])

    command.append(str(output_path))
    return command
