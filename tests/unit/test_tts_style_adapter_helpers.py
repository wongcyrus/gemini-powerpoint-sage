"""Tests for TTS style adapter helper functions."""

from services.tts.tts_style_adapter_helpers import (
    analyze_speaker_notes_to_style,
    build_base_tts_prompt,
    create_concise_prompt,
    create_fallback_prompt,
    detect_presentation_type,
    extract_style_indicators,
    get_default_professional_style,
)
from core.domain.tts import PresentationType


class TestTTSStyleAdapterHelpers:
    """Tests for pure TTS style helpers."""

    def test_build_base_prompt_and_default_style(self):
        """Base and default prompts should include the expected scaffolding."""
        assert "en-US" in build_base_tts_prompt("en-US")
        assert "Chinese, Mandarin (China)" in build_base_tts_prompt("yue-HK")
        assert "使用香港廣東話輸出" in build_base_tts_prompt("yue-HK")
        assert "professional" in get_default_professional_style()

    def test_detect_presentation_type_and_extract_indicators(self):
        """Style heuristics should detect tone and presentation type."""
        ptype = detect_presentation_type("research study", "methodology analysis")
        analysis = extract_style_indicators(
            "We should speak slowly and emphasize the key results with confidence.",
            "The research analysis is important.",
        )

        assert ptype == PresentationType.ACADEMIC
        assert analysis["tone"] in {"professional", "technical", "narrative"}
        assert analysis["pace"] == "slow"
        assert analysis["presentation_type"] == PresentationType.ACADEMIC
        assert analysis["confidence_score"] >= 0.3

    def test_style_guidelines_and_fallback_prompts(self):
        """Guideline text should feed the fallback prompt builders."""
        guidelines = analyze_speaker_notes_to_style("formal and technical", "architecture")
        fallback = create_fallback_prompt(guidelines, "ja")
        concise = create_concise_prompt(guidelines, "ja")
        cantonese_fallback = create_fallback_prompt(guidelines, "yue-HK")
        cantonese_concise = create_concise_prompt(guidelines, "yue-HK")

        assert "SPEAKING STYLE ANALYSIS" in guidelines
        assert "presentation in ja" in fallback
        assert concise.startswith("Speak in a ")
        assert "Chinese, Mandarin (China)" in cantonese_fallback
        assert "使用香港廣東話輸出" in cantonese_fallback
        assert "Chinese, Mandarin (China)" in cantonese_concise
