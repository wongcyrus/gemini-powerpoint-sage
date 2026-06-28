"""Tests for CLI utility helpers."""

from pathlib import Path

import pytest

from utils.cli_utils import parse_languages, resolve_pdf_path, resolve_pptx_path


class TestParseLanguages:
    """Tests for language parsing."""

    def test_parse_languages_inserts_english_when_missing(self):
        """English should be injected first when not explicitly provided."""
        assert parse_languages("zh-CN,ja") == ["en", "zh-CN", "ja"]

    def test_parse_languages_moves_english_to_front(self):
        """English should lead the processing order when present."""
        assert parse_languages("zh-CN,en,ja") == ["en", "zh-CN", "ja"]


class TestResolvePptxPath:
    """Tests for PPTX path resolution."""

    def test_resolve_pptx_path_returns_existing_file(self, tmp_path):
        """Existing PPTX files should resolve to an absolute path."""
        pptx_path = tmp_path / "deck.pptx"
        pptx_path.touch()

        assert resolve_pptx_path(str(pptx_path)) == str(pptx_path.resolve())

    def test_resolve_pptx_path_fuzzy_matches_collapsed_whitespace(self, tmp_path, monkeypatch):
        """Whitespace normalization should resolve user input to nearby files."""
        pptx_path = tmp_path / "My   Deck.pptx"
        pptx_path.touch()
        monkeypatch.chdir(tmp_path)

        resolved = resolve_pptx_path(str(tmp_path / "My Deck.pptx"))

        assert resolved == str(pptx_path.resolve())

    def test_resolve_pptx_path_raises_helpful_error(self, tmp_path):
        """Missing PPTX files should raise a helpful lookup error."""
        nearby = tmp_path / "Nearby Deck.pptx"
        nearby.touch()

        with pytest.raises(FileNotFoundError, match="PPTX/PPTM file not found"):
            resolve_pptx_path(str(tmp_path / "missing.pptx"))


class TestResolvePdfPath:
    """Tests for PDF path resolution."""

    def test_resolve_pdf_path_uses_explicit_same_directory_file(self, tmp_path):
        """Explicit PDFs in the PPTX directory should be accepted."""
        pptx_path = tmp_path / "deck.pptx"
        pdf_path = tmp_path / "deck.pdf"
        pptx_path.touch()
        pdf_path.touch()

        assert resolve_pdf_path(str(pdf_path), str(pptx_path)) == str(pdf_path.resolve())

    def test_resolve_pdf_path_rejects_explicit_other_directory_file(self, tmp_path, capsys):
        """Explicit PDFs outside the PPTX directory should be rejected."""
        pptx_path = tmp_path / "deck.pptx"
        other_dir = tmp_path / "other"
        pdf_path = other_dir / "deck.pdf"
        pptx_path.touch()
        other_dir.mkdir()
        pdf_path.touch()

        resolved = resolve_pdf_path(str(pdf_path), str(pptx_path))

        assert resolved is None
        assert "must be in the same folder" in capsys.readouterr().out

    def test_resolve_pdf_path_auto_detects_matching_pdf(self, tmp_path):
        """Absent explicit PDFs should fall back to same-name auto-detection."""
        pptx_path = tmp_path / "deck.pptx"
        pdf_path = tmp_path / "deck.pdf"
        pptx_path.touch()
        pdf_path.touch()

        assert resolve_pdf_path(None, str(pptx_path)) == str(pdf_path)
