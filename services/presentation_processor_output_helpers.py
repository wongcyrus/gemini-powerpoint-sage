"""Pure-ish helpers for presentation processor output saving."""

from __future__ import annotations

import os
import shutil
from typing import Callable, Optional, Tuple

from pptx import Presentation


def save_processed_presentations(
    prs_notes: Presentation,
    prs_visuals: Presentation,
    output_path_notes: str,
    output_path_visuals: str,
    source_pptx_path: str,
    missing_visuals_count: int,
    ensure_pptx_path: Callable[[str], str],
    restore_vba_project: Callable[[str, str, str], None],
) -> tuple[str, Optional[str]]:
    """Save processed presentations and return their final paths."""
    temp_notes_pptx = ensure_pptx_path(output_path_notes)
    prs_notes.save(temp_notes_pptx)

    src_ext = os.path.splitext(source_pptx_path)[1].lower()
    if src_ext == ".pptm" and output_path_notes.lower().endswith(".pptm"):
        restore_vba_project(source_pptx_path, temp_notes_pptx, output_path_notes)
    elif temp_notes_pptx != output_path_notes:
        shutil.move(temp_notes_pptx, output_path_notes)

    final_visuals_path: Optional[str] = None
    if missing_visuals_count == 0:
        temp_visuals_pptx = ensure_pptx_path(output_path_visuals)
        prs_visuals.save(temp_visuals_pptx)
        if src_ext == ".pptm" and output_path_visuals.lower().endswith(".pptm"):
            restore_vba_project(source_pptx_path, temp_visuals_pptx, output_path_visuals)
        elif temp_visuals_pptx != output_path_visuals:
            shutil.move(temp_visuals_pptx, output_path_visuals)
        final_visuals_path = output_path_visuals

    return output_path_notes, final_visuals_path
