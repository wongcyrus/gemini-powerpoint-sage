"""Helpers for presentation processor global context handling."""

from __future__ import annotations

import os
from typing import Any, Callable


async def get_global_context(
    *,
    pdf_doc,
    limit: int,
    progress: dict,
    language: str,
    retry_errors: bool,
    progress_file: str,
    output_dir: str,
    pptx_path: str,
    load_progress: Callable[[str], dict],
    save_progress: Callable[[str, dict], None],
    get_progress_file_path: Callable[[str, str, str], str],
    run_stateless_agent: Callable[..., object],
    overviewer_agent,
    translator_agent,
    build_generation_prompt: Callable[[int], str],
    build_translation_prompt: Callable[[str, str, str], str],
    language_name_lookup: Callable[[str], str],
) -> str:
    """Return cached, translated, or freshly generated global context."""
    if (
        "global_context" in progress
        and progress["global_context"]
        and len(progress["global_context"]) > 50
        and not retry_errors
    ):
        return progress["global_context"]

    if language != "en":
        en_progress_file = get_progress_file_path(pptx_path, "en", output_dir)
        if os.path.exists(en_progress_file):
            en_progress = load_progress(en_progress_file)
            en_global_context = en_progress.get("global_context")
            if en_global_context and len(en_global_context) > 50 and translator_agent:
                lang_name = language_name_lookup(language)
                translate_prompt = build_translation_prompt(
                    en_global_context,
                    lang_name,
                    language,
                )
                global_context = await run_stateless_agent(
                    translator_agent,
                    translate_prompt,
                )
                progress["global_context"] = global_context
                save_progress(progress_file, progress)
                return global_context

    all_images = []
    for i in range(limit):
        pix = pdf_doc[i].get_pixmap(dpi=75)
        from PIL import Image

        all_images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))

    generation_prompt = build_generation_prompt(len(all_images))
    global_context = await run_stateless_agent(
        overviewer_agent,
        generation_prompt,
        images=all_images,
    )
    progress["global_context"] = global_context
    save_progress(progress_file, progress)
    return global_context
