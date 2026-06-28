"""Tests for PowerPoint utility helpers."""

import zipfile
from pathlib import Path
from types import SimpleNamespace

from utils.pptx_utils import ensure_pptx_path, get_slide_notes, restore_vba_project, update_slide_notes


class TestPptxUtils:
    """Tests for PPTX helper functions."""

    def test_ensure_pptx_path_appends_extension_when_missing(self):
        """Paths without .pptx should get normalized."""
        assert ensure_pptx_path("deck") == "deck.pptx"
        assert ensure_pptx_path("deck.pptm") == "deck.pptx"
        assert ensure_pptx_path("deck.pptx") == "deck.pptx"

    def test_get_slide_notes_returns_text_or_empty_string(self):
        """Notes extraction should handle missing notes gracefully."""
        slide = SimpleNamespace(
            has_notes_slide=True,
            notes_slide=SimpleNamespace(notes_text_frame=SimpleNamespace(text="  hello world  ")),
        )
        empty_slide = SimpleNamespace(has_notes_slide=False, notes_slide=None)

        assert get_slide_notes(slide) == "hello world"
        assert get_slide_notes(empty_slide) == ""

    def test_update_slide_notes_writes_plain_text(self):
        """Slide notes should be written without bullet formatting."""
        paragraph = SimpleNamespace(text="", level=None, alignment=None)
        text_frame = SimpleNamespace(paragraphs=[paragraph], clear=lambda: None)
        slide = SimpleNamespace(has_notes_slide=False, notes_slide=SimpleNamespace(notes_text_frame=text_frame))

        update_slide_notes(slide, "Updated notes")

        assert paragraph.text == "Updated notes"
        assert paragraph.level == 0

    def test_restore_vba_project_moves_generated_pptx_when_no_macro_exists(self, tmp_path):
        """When no VBA project exists, the generated file should simply be moved."""
        original_src = tmp_path / "source.pptm"
        generated_pptx = tmp_path / "generated.pptx"
        final_path = tmp_path / "final.pptm"

        with zipfile.ZipFile(original_src, "w") as zf:
            zf.writestr("ppt/presentation.xml", "<xml />")
        with zipfile.ZipFile(generated_pptx, "w") as zf:
            zf.writestr("ppt/presentation.xml", "<xml />")

        restore_vba_project(str(original_src), str(generated_pptx), str(final_path))

        assert final_path.exists()
        assert not generated_pptx.exists()

    def test_restore_vba_project_falls_back_to_move_on_error(self, monkeypatch, tmp_path):
        """Unexpected archive failures should fall back to a plain file move."""
        original_src = tmp_path / "source.pptm"
        generated_pptx = tmp_path / "generated.pptx"
        final_path = tmp_path / "final.pptm"
        generated_pptx.write_bytes(b"generated")

        monkeypatch.setattr("utils.pptx_utils.zipfile.ZipFile", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

        restore_vba_project(str(original_src), str(generated_pptx), str(final_path))

        assert final_path.read_bytes() == b"generated"
