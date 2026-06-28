"""Pure helpers for presentation processor TTS preparation."""

from __future__ import annotations

from typing import Iterable, List, Mapping

from core.domain.tts import SlideData


def build_tts_slide_data(
    slide_data: Iterable[Mapping[str, object]],
    language_code: str,
    presentation_id: str,
) -> List[SlideData]:
    """Build TTS slide models from processed presentation slide data."""
    tts_slides: List[SlideData] = []
    for slide_info in slide_data:
        if slide_info.get("status") == "success" and slide_info.get("speaker_notes"):
            tts_slides.append(
                SlideData(
                    slide_number=int(slide_info["slide_idx"]),
                    text_content=str(slide_info["speaker_notes"]),
                    speaker_notes=str(slide_info["speaker_notes"]),
                    language_code=language_code,
                    presentation_id=presentation_id,
                )
            )
    return tts_slides
