"""Tests for TTS CLI utilities."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

import utils.tts_cli_utils as tts_cli_utils
from core.domain.tts import TTSEngineType, TTSResult


class TestTTSCLIParser:
    """Tests for the CLI parser."""

    def test_create_tts_cli_parser_defines_expected_commands(self):
        """The parser should expose all documented subcommands."""
        parser = tts_cli_utils.create_tts_cli_parser()

        assert parser.parse_args(["generate", "deck.json"]).command == "generate"
        assert parser.parse_args(["test"]).command == "test"
        assert parser.parse_args(["cleanup"]).command == "cleanup"
        assert parser.parse_args(["stats"]).command == "stats"


class TestTTSCLIUtility:
    """Tests for TTSCLIUtility wrappers."""

    @pytest.fixture
    def utility(self):
        utility = tts_cli_utils.TTSCLIUtility()
        utility.tts_config = Mock(enabled=True)
        return utility

    @pytest.mark.asyncio
    async def test_generate_tts_for_presentation_builds_summary(self, utility, tmp_path):
        """Progress JSON should be converted into slide data and summarized."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(
            json.dumps(
                {
                    "slides": {
                        "slide_1": {"status": "success", "note": "First note", "slide_index": 1},
                        "slide_2": {"status": "failed", "note": "", "slide_index": 2},
                        "slide_3": {"status": "success", "note": "Third note", "slide_index": 3},
                    }
                }
            ),
            encoding="utf-8",
        )

        utility.orchestrator = Mock()
        utility.orchestrator.process_single_language_batch = AsyncMock(
            return_value=[
                TTSResult(audio_data=b"abc", file_path="/tmp/a.mp3", engine_used=TTSEngineType.GEMINI),
                TTSResult(metadata={"error": "boom"}, engine_used=TTSEngineType.TRADITIONAL),
            ]
        )

        result = await utility.generate_tts_for_presentation(str(progress_file), language="ja-JP")

        assert result["presentation_id"] == "progress"
        assert result["language"] == "ja-JP"
        assert result["total_slides"] == 2
        assert result["successful"] == 1
        assert result["failed"] == 1
        assert [item["slide_number"] for item in result["results"]] == [1, 3]
        utility.orchestrator.process_single_language_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_tts_for_presentation_rejects_empty_progress(self, utility, tmp_path):
        """Progress files without valid notes should fail fast."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text(json.dumps({"slides": {"slide_1": {"status": "failed", "note": ""}}}), encoding="utf-8")
        utility.orchestrator = Mock()

        with pytest.raises(ValueError, match="No valid slides"):
            await utility.generate_tts_for_presentation(str(progress_file))

    @pytest.mark.asyncio
    async def test_test_tts_engines_reports_each_language(self, utility):
        """Engine smoke tests should summarize each language independently."""
        utility.orchestrator = Mock()
        utility.orchestrator.generate_speech_for_slide = AsyncMock(side_effect=[
            TTSResult(audio_data=b"abc", file_path="/tmp/en.mp3", engine_used=TTSEngineType.GEMINI),
            TTSResult(metadata={"error": "boom"}, engine_used=TTSEngineType.TRADITIONAL),
            RuntimeError("offline"),
        ])

        result = await utility.test_tts_engines()

        assert result["test_text"].startswith("This is a test")
        assert result["languages"]["en-US"]["success"] is True
        assert result["languages"]["ja-JP"]["success"] is False
        assert result["languages"]["yue-HK"]["success"] is False

    @pytest.mark.asyncio
    async def test_cleanup_cache_returns_cleanup_counts(self, utility):
        """Cache cleanup should combine cache and storage results."""
        utility.orchestrator = Mock()
        utility.orchestrator.cache_manager.cleanup_expired_entries = AsyncMock(return_value=4)
        utility.orchestrator.storage_manager.cleanup_old_files = Mock(return_value=2)

        result = await utility.cleanup_cache(max_age_days=10)

        assert result == {
            "cache_entries_cleaned": 4,
            "storage_files_cleaned": 2,
            "max_age_days": 10,
        }

    def test_get_tts_stats_returns_error_before_initialization(self, utility):
        """Stats should report an error if the orchestrator has not been set up."""
        utility.orchestrator = None

        assert utility.get_tts_stats() == {"error": "TTS orchestrator not initialized"}

    def test_get_tts_stats_delegates_to_orchestrator(self, utility):
        """Stats should be proxied from the orchestrator."""
        utility.orchestrator = Mock()
        utility.orchestrator.get_orchestrator_stats.return_value = {"queued": 3}

        assert utility.get_tts_stats() == {"queued": 3}
