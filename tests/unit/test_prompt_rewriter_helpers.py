"""Tests for prompt rewriter helper functions."""

from services.prompt_rewriter_helpers import (
    create_concise_tts_prompt,
    create_tts_fallback_prompt,
    validate_and_fix_tts_tone,
)


class TestPromptRewriterHelpers:
    """Tests for deterministic prompt rewriting helpers."""

    def test_validate_and_fix_tts_tone(self):
        """Invalid tones should be prefixed with professional guidance."""
        assert validate_and_fix_tts_tone("Speak vividly.") == "Speak in a professional manner. Speak vividly."
        assert validate_and_fix_tts_tone("Speak in a technical manner.") == "Speak in a technical manner."

    def test_create_tts_fallback_prompt(self):
        """Fallback prompts should derive tone and pace from guidelines."""
        prompt = create_tts_fallback_prompt("Detected Tone: casual\nPace Indicators: fast")

        assert prompt == "Speak in a casual manner. Speak at a brisk but clear pace."

    def test_create_concise_tts_prompt(self):
        """Concise prompts should compress the key style signals."""
        prompt = create_concise_tts_prompt(
            "Detected Tone: enthusiastic\nPace Indicators: slow\nEmphasis Points: safety, speed\nEmotional Context: confident"
        )

        assert "energetic and passionate" in prompt
        assert "slow, deliberate pace" in prompt
        assert len(prompt) <= 200
