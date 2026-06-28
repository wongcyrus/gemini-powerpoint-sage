"""Tests for presentation processor output helpers."""

from unittest.mock import Mock

from services.presentation_processor_output_helpers import save_processed_presentations


class TestPresentationProcessorOutputHelpers:
    """Tests for presentation export helpers."""

    def test_save_processed_presentations_saves_notes_and_visuals(self, tmp_path, monkeypatch):
        notes_path = str(tmp_path / "notes.pptx")
        visuals_path = str(tmp_path / "visuals.pptx")
        source_path = str(tmp_path / "source.pptx")
        (tmp_path / "source.pptx").write_text("src")

        notes_prs = Mock()
        visuals_prs = Mock()
        ensure_pptx_path = lambda path: path + ".tmp"
        restore_vba_project = Mock()
        moves = []
        monkeypatch.setattr("services.presentation_processor_output_helpers.shutil.move", lambda src, dst: moves.append((src, dst)))

        final_notes, final_visuals = save_processed_presentations(
            prs_notes=notes_prs,
            prs_visuals=visuals_prs,
            output_path_notes=notes_path,
            output_path_visuals=visuals_path,
            source_pptx_path=source_path,
            missing_visuals_count=0,
            ensure_pptx_path=ensure_pptx_path,
            restore_vba_project=restore_vba_project,
        )

        assert final_notes == notes_path
        assert final_visuals == visuals_path
        notes_prs.save.assert_called_once_with(notes_path + ".tmp")
        visuals_prs.save.assert_called_once_with(visuals_path + ".tmp")
        restore_vba_project.assert_not_called()
        assert moves == [(notes_path + ".tmp", notes_path), (visuals_path + ".tmp", visuals_path)]

    def test_save_processed_presentations_uses_pptm_restore(self, tmp_path, monkeypatch):
        notes_path = str(tmp_path / "notes.pptm")
        visuals_path = str(tmp_path / "visuals.pptm")
        source_path = str(tmp_path / "source.pptm")
        (tmp_path / "source.pptm").write_text("src")

        notes_prs = Mock()
        visuals_prs = Mock()
        ensure_pptx_path = lambda path: path + ".tmp"
        restore_vba_project = Mock()
        moves = []
        monkeypatch.setattr("services.presentation_processor_output_helpers.shutil.move", lambda src, dst: moves.append((src, dst)))

        final_notes, final_visuals = save_processed_presentations(
            prs_notes=notes_prs,
            prs_visuals=visuals_prs,
            output_path_notes=notes_path,
            output_path_visuals=visuals_path,
            source_pptx_path=source_path,
            missing_visuals_count=1,
            ensure_pptx_path=ensure_pptx_path,
            restore_vba_project=restore_vba_project,
        )

        assert final_notes == notes_path
        assert final_visuals is None
        restore_vba_project.assert_called_once_with(source_path, notes_path + ".tmp", notes_path)
        assert moves == []
