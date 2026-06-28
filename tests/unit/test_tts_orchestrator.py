"""Tests for TTS orchestrator behavior."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.domain.tts import SlideData, TTSEngineType, TTSResult
from services.tts.tts_orchestrator import TTSOrchestrator


def _make_orchestrator(tmp_path: Path) -> TTSOrchestrator:
    orchestrator = TTSOrchestrator.__new__(TTSOrchestrator)
    orchestrator.config = Mock(
        enabled=True,
        normalize_language_code=lambda value: "en-US" if value == "en" else value,
    )
    orchestrator.style_adapter = Mock(
        analyze_speaker_notes=Mock(return_value=Mock()),
        generate_tts_style_prompt=Mock(return_value="style"),
        analyze_presentation_style=Mock(return_value="presentation-style"),
    )
    orchestrator.engine_selector = Mock(
        select_engine=Mock(return_value=TTSEngineType.GEMINI),
        get_voice_config=Mock(return_value=Mock()),
    )
    orchestrator.cache_manager = Mock(generate_cache_key=Mock(return_value="abc123"))
    orchestrator.storage_manager = Mock(
        get_audio_file_path=Mock(return_value=str(tmp_path / "slide_1_abc123.mp3")),
        save_audio_file=AsyncMock(return_value=str(tmp_path / "slide_1_abc123.mp3")),
        create_local_directory_structure=Mock(),
    )
    orchestrator.gemini_engine = AsyncMock()
    orchestrator.traditional_engine = AsyncMock()
    orchestrator.gemini_semaphore = AsyncMock()
    orchestrator.traditional_semaphore = AsyncMock()
    return orchestrator


class TestTTSOrchestrator:
    """Tests for orchestration behavior."""

    def test_check_and_adjust_engine_for_size(self, tmp_path):
        """Large content should fall back from Gemini to Traditional."""
        orchestrator = _make_orchestrator(tmp_path)

        with patch("utils.text_processing.check_gemini_tts_size_limit", return_value=False):
            engine = orchestrator._check_and_adjust_engine_for_size("text", "notes", TTSEngineType.GEMINI, 1)

        assert engine == TTSEngineType.TRADITIONAL

    @pytest.mark.asyncio
    async def test_generate_speech_for_slide_uses_cached_file(self, tmp_path):
        """Existing audio files should be reused without regeneration."""
        orchestrator = _make_orchestrator(tmp_path)
        cached = tmp_path / "slide_1_abc123.mp3"
        cached.write_bytes(b"audio")

        result = await orchestrator.generate_speech_for_slide(1, "content", "notes", "en", "deck-1")

        assert result.metadata["cached"] is True
        assert result.has_file() is True

    @pytest.mark.asyncio
    async def test_process_presentation_batch_handles_disabled_and_enabled(self, tmp_path):
        """Batch processing should short-circuit when disabled and group results by language."""
        orchestrator = _make_orchestrator(tmp_path)
        slide = SlideData(slide_number=1, text_content="hello", speaker_notes="notes")

        orchestrator.config.enabled = False
        assert await orchestrator.process_presentation_batch([slide], ["en"], "deck-1") == {}

        orchestrator.config.enabled = True
        orchestrator.generate_speech_for_slide = AsyncMock(
            return_value=TTSResult(audio_data=b"audio", file_path=str(tmp_path / "a.mp3"))
        )

        results = await orchestrator.process_presentation_batch([slide], ["en", "zh-CN"], "deck-1")

        assert set(results.keys()) == {"en", "zh-CN"}
        assert all(results[lang] for lang in results)
        orchestrator.style_adapter.analyze_presentation_style.assert_called()
        orchestrator.storage_manager.create_local_directory_structure.assert_called_once()
