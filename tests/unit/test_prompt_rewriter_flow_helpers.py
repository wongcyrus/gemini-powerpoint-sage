"""Tests for prompt rewriter flow helpers."""

from services.prompt_rewriter_flow_helpers import (
    build_emergency_fallback_prompt,
    build_rewrite_request,
)


class TestPromptRewriterFlowHelpers:
    """Tests for prompt request builders."""

    def test_build_rewrite_request_for_tts(self):
        """TTS requests should include the TTS-specific constraints."""
        request = build_rewrite_request("base", "style", "tts")

        assert "STYLE_TYPE: tts_speech" in request
        assert "IMPORTANT TONE CONSTRAINT" in request
        assert "base" in request

    def test_build_rewrite_request_for_designer_and_other_types(self):
        """Designer requests should use the visual branch and others should use speaker."""
        designer = build_rewrite_request("base", "style", "designer")
        writer = build_rewrite_request("base", "style", "writer")

        assert "STYLE_TYPE: visual" in designer
        assert "STYLE_TYPE: speaker" in writer

    def test_build_emergency_fallback_prompt(self):
        """Emergency fallback prompts should preserve the style payload."""
        prompt = build_emergency_fallback_prompt("base", "style", "writer")

        assert "STYLE INTEGRATION (WRITER)" in prompt
        assert "Apply these style guidelines" in prompt
        assert "base" in prompt
