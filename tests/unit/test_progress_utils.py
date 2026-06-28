"""Tests for progress tracking utilities."""

import json
import os

from utils.progress_utils import (
    create_slide_key,
    get_progress_file_path,
    load_progress,
    save_progress,
    should_retry_errors,
)


class TestProgressUtils:
    """Tests for progress file helpers."""

    def test_load_progress_returns_empty_structure_for_missing_file(self, tmp_path):
        """Missing progress files should produce the default empty structure."""
        assert load_progress(str(tmp_path / "missing.json")) == {"slides": {}}

    def test_load_progress_reads_existing_json(self, tmp_path):
        """Existing progress JSON should be loaded as-is."""
        path = tmp_path / "progress.json"
        payload = {"slides": {"slide_1": {"note": "hello"}}}
        path.write_text(json.dumps(payload), encoding="utf-8")

        assert load_progress(str(path)) == payload

    def test_save_progress_writes_json_atomically(self, tmp_path):
        """Saving progress should persist the JSON payload to disk."""
        path = tmp_path / "progress.json"
        payload = {"slides": {"slide_1": {"note": "hello"}}}

        save_progress(str(path), payload)

        assert json.loads(path.read_text(encoding="utf-8")) == payload

    def test_create_slide_key_hashes_note_content(self):
        """Slide keys should include a stable content hash."""
        key = create_slide_key(3, "Hello world")

        assert key.startswith("slide_3_")
        assert len(key.split("_")[-1]) == 8

    def test_get_progress_file_path_prefers_environment_override(self, tmp_path, monkeypatch):
        """Configured env overrides should win over derived progress paths."""
        override = tmp_path / "override.json"
        monkeypatch.setenv("SPEAKER_NOTE_PROGRESS_FILE", str(override))

        resolved = get_progress_file_path(str(tmp_path / "deck.pptx"), language="ja")

        assert resolved == str(override)

    def test_get_progress_file_path_builds_default_generate_path(self, tmp_path, monkeypatch):
        """Without overrides the path should be derived from the PPTX name and language."""
        monkeypatch.delenv("SPEAKER_NOTE_PROGRESS_FILE", raising=False)
        pptx_path = tmp_path / "deck.pptx"
        pptx_path.touch()

        resolved = get_progress_file_path(str(pptx_path), language="zh-CN")

        assert resolved.endswith(os.path.join("generate", "deck_zh-CN_progress.json"))
        assert (tmp_path / "generate").exists()

    def test_should_retry_errors_reads_boolean_env_flag(self, monkeypatch):
        """Retry mode should be driven by the configured environment flag."""
        monkeypatch.setenv("SPEAKER_NOTE_RETRY_ERRORS", "true")
        assert should_retry_errors() is True
        monkeypatch.setenv("SPEAKER_NOTE_RETRY_ERRORS", "false")
        assert should_retry_errors() is False
