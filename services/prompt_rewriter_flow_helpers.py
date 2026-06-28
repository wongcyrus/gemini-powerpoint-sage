"""Pure helpers for prompt rewriter request construction."""

from __future__ import annotations


def build_rewrite_request(base_prompt: str, style_guidelines: str, prompt_type: str) -> str:
    """Build the LLM rewrite request for a given prompt type."""
    if prompt_type == "tts":
        return f"""BASE_PROMPT:
{base_prompt}

STYLE_GUIDELINES:
{style_guidelines}

STYLE_TYPE: tts_speech

CRITICAL REQUIREMENT: This is for text-to-speech generation using Gemini TTS. The output should be a natural language instruction that tells the TTS engine how to speak the content.

IMPORTANT TONE CONSTRAINT: The tone MUST be exactly one of these values: 'professional', 'casual', 'enthusiastic', 'technical', or 'narrative'. Do not use any other tone words.

IMPORTANT LENGTH CONSTRAINT: The final output MUST be under 500 characters total. Be extremely concise.

Focus on:
1. Choose the most appropriate tone from: professional, casual, enthusiastic, technical, narrative
2. Pace and rhythm instructions (slow, normal, fast)
3. Emphasis and emotional expression
4. Language-appropriate cultural considerations

Please rewrite the base prompt to create a SHORT, natural language TTS instruction that incorporates the speaking style from the guidelines. Keep it under 500 characters and use only the allowed tone values."""

    return f"""BASE_PROMPT:
{base_prompt}

STYLE_GUIDELINES:
{style_guidelines}

STYLE_TYPE: {"visual" if prompt_type == "designer" else "speaker"}

Please rewrite the base prompt to deeply integrate the style guidelines throughout the instructions."""


def build_emergency_fallback_prompt(base_prompt: str, style_guidelines: str, prompt_type: str) -> str:
    """Build the emergency fallback prompt when rewriting fails catastrophically."""
    return f"""{base_prompt}

===============================================================================
STYLE INTEGRATION ({prompt_type.upper()})
===============================================================================

{style_guidelines}

Apply these style guidelines throughout all operations."""
