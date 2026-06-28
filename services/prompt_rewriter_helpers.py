"""Pure helpers for prompt rewriting behavior."""

from __future__ import annotations


def validate_and_fix_tts_tone(tts_prompt: str) -> str:
    """Ensure a TTS prompt contains one of the allowed tone values."""
    valid_tones = ["professional", "casual", "enthusiastic", "technical", "narrative"]
    for tone in valid_tones:
        if tone in tts_prompt.lower():
            return tts_prompt
    return f"Speak in a professional manner. {tts_prompt}"


def create_tts_fallback_prompt(style_guidelines: str) -> str:
    """Create a short TTS fallback prompt from style guidelines."""
    tone = "professional"
    pace = "normal"

    for line in style_guidelines.split("\n"):
        if "Detected Tone:" in line:
            detected = line.split(":", 1)[1].strip().lower()
            if detected in ["professional", "casual", "enthusiastic", "technical", "narrative"]:
                tone = detected
        elif "Pace Indicators:" in line:
            pace_part = line.split(":", 1)[1].strip().lower()
            if pace_part in ["slow", "fast"]:
                pace = pace_part

    pace_instruction = ""
    if pace == "slow":
        pace_instruction = " Speak slowly and clearly."
    elif pace == "fast":
        pace_instruction = " Speak at a brisk but clear pace."

    return f"Speak in a {tone} manner.{pace_instruction}"


def create_concise_tts_prompt(style_guidelines: str) -> str:
    """Create a concise TTS prompt under the Gemini length budget."""
    lines = style_guidelines.split("\n")
    tone = "professional"
    pace = "normal"
    emphasis_words = []
    emotions = []

    for line in lines:
        if "Detected Tone:" in line:
            tone = line.split(":", 1)[1].strip().lower()
        elif "Pace Indicators:" in line:
            pace = line.split(":", 1)[1].strip().lower()
        elif "Emphasis Points:" in line and "None" not in line:
            emphasis_part = line.split(":", 1)[1].strip()
            if emphasis_part and emphasis_part != "None":
                emphasis_words = [w.strip() for w in emphasis_part.split(",")][:2]
        elif "Emotional Context:" in line and "Neutral" not in line:
            emotion_part = line.split(":", 1)[1].strip()
            if emotion_part and emotion_part != "Neutral":
                emotions = [emotion_part.lower()]

    tone_map = {
        "professional": "professional and clear",
        "enthusiastic": "energetic and passionate",
        "casual": "friendly and conversational",
        "technical": "precise and methodical",
        "formal": "authoritative and structured",
        "narrative": "engaging storytelling",
    }
    base_tone = tone_map.get(tone, "clear and professional")

    components = [f"Speak in a {base_tone} manner"]
    if pace == "slow":
        components.append("at a slow, deliberate pace")
    elif pace == "fast":
        components.append("at a brisk pace")
    if emotions:
        components.append(f"with {emotions[0]} emotion")
    if emphasis_words:
        components.append(f"emphasizing {emphasis_words[0]}")

    prompt = ". ".join(components) + "."
    if len(prompt) > 200:
        prompt = f"Speak in a {base_tone} manner."
    return prompt
