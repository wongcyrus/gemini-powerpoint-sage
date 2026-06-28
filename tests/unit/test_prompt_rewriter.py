"""Tests for prompt rewriter helpers and cache integration."""

from unittest.mock import AsyncMock, Mock

import pytest

from services.prompt_rewriter import PromptRewriter


class TestPromptRewriter:
    """Tests for deterministic prompt rewriting helpers."""

    def _make_rewriter(self):
        rewriter = object.__new__(PromptRewriter)
        rewriter.visual_style = "Cyberpunk visual style"
        rewriter.speaker_style = "Teacher speaking style"
        rewriter.cache = Mock()
        rewriter.cache.get_cache_stats.return_value = {"enabled": True, "cache_hits": 1}
        return rewriter

    def test_fallback_to_simple_concatenation_for_writer_adds_language_rules(self):
        """Writer-style fallback should inject strict language compliance instructions."""
        rewriter = self._make_rewriter()
        request = (
            "BASE_PROMPT:\nBase writer prompt\n"
            "STYLE_GUIDELINES:\nSpeaker rules\n"
            "STYLE_TYPE: speaker\n"
        )

        rewritten = rewriter._fallback_to_simple_concatenation(request, "writer_rewriter")

        assert "MANDATORY LANGUAGE COMPLIANCE" in rewritten
        assert "Speaker rules" in rewritten

    def test_fallback_to_simple_concatenation_for_designer_adds_visual_section(self):
        """Current substring matching routes designer_rewriter through the writer-style fallback block."""
        rewriter = self._make_rewriter()
        request = (
            "BASE_PROMPT:\nBase designer prompt\n"
            "STYLE_GUIDELINES:\nVisual rules\n"
            "STYLE_TYPE: visual\n"
        )

        rewritten = rewriter._fallback_to_simple_concatenation(request, "designer_rewriter")

        assert "STYLE INTEGRATION (VISUAL)" in rewritten
        assert "MANDATORY LANGUAGE COMPLIANCE" in rewritten
        assert "Visual rules" in rewritten

    def test_validate_and_fix_tts_tone_defaults_to_professional(self):
        """Missing allowed tones should be normalized to professional."""
        rewriter = self._make_rewriter()

        fixed = rewriter._validate_and_fix_tts_tone("Speak with gravitas and flair.")

        assert fixed.startswith("Speak in a professional manner.")

    def test_create_tts_fallback_prompt_extracts_tone_and_pace(self):
        """Fallback TTS prompt should derive tone and pace from style analysis."""
        rewriter = self._make_rewriter()
        guidelines = "Detected Tone: enthusiastic\nPace Indicators: fast\n"

        prompt = rewriter._create_tts_fallback_prompt("base", guidelines)

        assert "enthusiastic" in prompt
        assert "brisk" in prompt

    def test_create_concise_tts_prompt_builds_short_instruction(self):
        """Concise TTS prompts should compress key style signals into one sentence."""
        rewriter = self._make_rewriter()
        guidelines = (
            "Detected Tone: technical\n"
            "Pace Indicators: slow\n"
            "Emphasis Points: security, encryption\n"
            "Emotional Context: confident\n"
        )

        prompt = rewriter._create_concise_tts_prompt(guidelines)

        assert "technical" in prompt or "methodical" in prompt
        assert len(prompt) <= 200

    def test_get_rewrite_summary_includes_style_lengths_and_cache_stats(self):
        """Rewrite summaries should expose style previews and cache information."""
        rewriter = self._make_rewriter()

        summary = rewriter.get_rewrite_summary()

        assert summary["visual_style_length"] == len("Cyberpunk visual style")
        assert summary["speaker_style_length"] == len("Teacher speaking style")
        assert summary["cache_stats"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_rewrite_with_cache_returns_cached_prompt_without_llm_call(self):
        """Cache hits should bypass expensive LLM rewriting."""
        rewriter = self._make_rewriter()
        rewriter.cache.generate_cache_key.return_value = "writer_key"
        rewriter.cache.get_cached_prompt.return_value = "cached prompt"

        rewritten = await rewriter._rewrite_with_cache("base", "style", "writer")

        assert rewritten == "cached prompt"
        rewriter.cache.store_prompt.assert_not_called()

    @pytest.mark.asyncio
    async def test_rewrite_with_cache_stores_llm_rewrite_result(self):
        """Cache misses should run the rewriter and then store the result."""
        rewriter = self._make_rewriter()
        rewriter.cache.generate_cache_key.return_value = "designer_key"
        rewriter.cache.get_cached_prompt.return_value = None
        rewriter.cache.store_prompt.return_value = True
        rewriter._run_rewriter_with_retry = AsyncMock(return_value="llm result")

        rewritten = await rewriter._rewrite_with_cache("base", "style", "designer")

        assert rewritten == "llm result"
        rewriter.cache.store_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_rewrite_with_cache_falls_back_when_llm_fails(self):
        """LLM rewrite failures should fall back to deterministic concatenation."""
        rewriter = self._make_rewriter()
        rewriter.cache.generate_cache_key.return_value = "tts_key"
        rewriter.cache.get_cached_prompt.return_value = None
        rewriter._run_rewriter_with_retry = AsyncMock(side_effect=RuntimeError("boom"))

        rewritten = await rewriter._rewrite_with_cache("base", "Detected Tone: casual", "tts")

        assert "Detected Tone: casual" in rewritten
        assert "MANDATORY LANGUAGE COMPLIANCE" in rewritten

    @pytest.mark.asyncio
    async def test_rewrite_tts_prompt_applies_tone_fix_and_length_guard(self):
        """TTS rewriting should validate tone and shorten overlong prompts."""
        rewriter = self._make_rewriter()
        rewriter._rewrite_with_cache = AsyncMock(return_value="x" * 3600)
        rewriter._create_concise_tts_prompt = Mock(return_value="Speak in a professional and clear manner.")

        rewritten = await rewriter.rewrite_tts_prompt("base", "Detected Tone: professional")

        assert rewritten == "Speak in a professional and clear manner."
