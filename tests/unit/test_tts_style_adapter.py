"""Tests for TTSStyleAdapter."""

from unittest.mock import Mock

from services.tts.tts_style_adapter import TTSStyleAdapter


class TestTTSStyleAdapter:
    """Tests for adapter caching and prompt generation."""

    def _make_adapter(self, rewrite_side_effect=None):
        rewriter = Mock()
        if rewrite_side_effect is None:
            rewriter.rewrite_tts_prompt.return_value = "rewritten prompt"
        else:
            rewriter.rewrite_tts_prompt.side_effect = rewrite_side_effect
        return TTSStyleAdapter(rewriter)

    def test_generate_tts_style_prompt_caches_by_presentation(self):
        """Repeated requests for the same presentation should reuse cached prompts."""
        adapter = self._make_adapter()

        prompt1 = adapter.generate_tts_style_prompt("notes", "content", "en-US", presentation_id="deck-1")
        prompt2 = adapter.generate_tts_style_prompt("notes", "content", "en-US", presentation_id="deck-1")

        assert prompt1 == "rewritten prompt"
        assert prompt2 == "rewritten prompt"
        assert adapter.prompt_rewriter.rewrite_tts_prompt.call_count == 1

    def test_generate_tts_style_prompt_falls_back_on_long_output(self):
        """Too-long prompts should be replaced with a concise fallback."""
        adapter = self._make_adapter(rewrite_side_effect=lambda *_: "x" * 4001)

        prompt = adapter.generate_tts_style_prompt("formal notes", "content", "en-US", presentation_id="deck-2")

        assert prompt.startswith("Speak in a ")
        assert len(prompt) < 200

    def test_analyze_and_clear_cache(self):
        """Speaker note analysis and cache clearing should work independently."""
        adapter = self._make_adapter()

        style_context = adapter.analyze_speaker_notes("technical and precise", "architecture system")
        assert style_context.pace in {"normal", "slow", "fast"}
        assert style_context.presentation_type.value in {"business", "academic", "training", "technical", "narrative"}

        adapter.generate_tts_style_prompt("notes", "content", "en-US", presentation_id="deck-3")
        assert adapter._style_cache
        adapter.clear_style_cache("deck-3")
        assert adapter._style_cache == {}
