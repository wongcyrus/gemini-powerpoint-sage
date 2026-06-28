"""Pure helpers for video synthesis orchestration."""

from __future__ import annotations

import re


def extract_slide_number_from_filenames(image_name: str, audio_name: str) -> int:
    """Extract and validate the slide number from paired filenames."""
    image_match = re.search(r"slide_(\d+)", image_name)
    if not image_match:
        raise ValueError(f"Cannot extract slide number from image filename: {image_name}")
    image_slide_num = int(image_match.group(1))

    audio_match = re.search(r"slide_(\d+)", audio_name)
    if not audio_match:
        raise ValueError(f"Cannot extract slide number from audio filename: {audio_name}")
    audio_slide_num = int(audio_match.group(1))

    if image_slide_num != audio_slide_num:
        raise ValueError(
            f"Slide number mismatch: image has slide {image_slide_num}, audio has slide {audio_slide_num}"
        )

    return image_slide_num
