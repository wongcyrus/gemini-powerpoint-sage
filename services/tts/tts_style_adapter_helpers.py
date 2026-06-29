"""Pure helpers for TTS style analysis and prompt construction."""

from __future__ import annotations

from core.domain.tts import PresentationType


def build_base_tts_prompt(language_code: str) -> str:
    """Create the base prompt template for TTS rewriting."""
    if language_code in {"yue-HK", "zh-HK", "yue"}:
        return (
            "You are a professional speaker delivering presentation content in Chinese, Mandarin (China).\n"
            "Use Hong Kong Cantonese pronunciation and phrasing.\n"
            "System prompt: 使用香港廣東話輸出\n"
            "Your goal is to communicate clearly and effectively to your audience.\n"
            "Speak the following content with appropriate tone and delivery."
        )

    return (
        f"You are a professional speaker delivering presentation content in {language_code}. \n"
        "Your goal is to communicate clearly and effectively to your audience. \n"
        "Speak the following content with appropriate tone and delivery."
    )


def get_default_professional_style() -> str:
    """Return the default style guideline block."""
    return """SPEAKING STYLE ANALYSIS:

Detected Tone: professional
Pace Indicators: normal
Emphasis Points: None
Emotional Context: Neutral
Presentation Type: business

STYLE GUIDELINES:
Professional, clear, and authoritative delivery appropriate for business presentations. 
Maintain engagement while conveying information accurately and efficiently.

DELIVERY INSTRUCTIONS:
Use clear, natural delivery with appropriate pacing for comprehension."""


def detect_presentation_type(notes: str, content: str) -> PresentationType:
    """Detect presentation type from combined text."""
    type_indicators = {
        PresentationType.ACADEMIC: ["research", "study", "analysis", "theory", "methodology"],
        PresentationType.BUSINESS: ["strategy", "revenue", "market", "growth", "profit"],
        PresentationType.TRAINING: ["learn", "practice", "skill", "procedure", "exercise"],
        PresentationType.TECHNICAL: ["system", "implementation", "configuration", "architecture"],
        PresentationType.NARRATIVE: ["story", "journey", "experience", "example", "case"],
    }

    combined = f"{notes} {content}"
    type_scores = {}

    for ptype, indicators in type_indicators.items():
        score = sum(1 for indicator in indicators if indicator in combined)
        if score > 0:
            type_scores[ptype] = score

    return max(type_scores, key=type_scores.get) if type_scores else PresentationType.BUSINESS


def extract_style_indicators(speaker_notes: str, slide_content: str) -> dict:
    """Extract style heuristics from speaker notes and slide content."""
    normalized_notes = speaker_notes.lower().strip()
    normalized_content = slide_content.lower().strip()

    style_patterns = {
        "professional": ["formal", "professional", "academic", "official", "structured"],
        "casual": ["casual", "informal", "conversational", "friendly", "relaxed"],
        "enthusiastic": ["exciting", "energetic", "passionate", "dynamic", "enthusiastic"],
        "technical": ["technical", "detailed", "precise", "step-by-step", "systematic"],
        "narrative": ["story", "narrative", "journey", "experience", "example"],
    }

    tone_scores = {}
    for tone, patterns in style_patterns.items():
        score = sum(1 for pattern in patterns if pattern in normalized_notes or pattern in normalized_content)
        if score > 0:
            tone_scores[tone] = score

    dominant_tone = max(tone_scores, key=tone_scores.get) if tone_scores else "professional"
    total_matches = sum(tone_scores.values())
    confidence_score = min(0.9, max(0.3, total_matches / 10))

    pace = "normal"
    if any(word in normalized_notes for word in ["slowly", "carefully", "pause", "deliberate"]):
        pace = "slow"
    elif any(word in normalized_notes for word in ["quickly", "rapidly", "brief", "fast"]):
        pace = "fast"

    emphasis_words = []
    emphasis_triggers = ["important", "key", "critical", "emphasize", "highlight", "focus"]
    for trigger in emphasis_triggers:
        if trigger in normalized_notes:
            words = normalized_notes.split()
            for i, word in enumerate(words):
                if trigger in word:
                    for j in range(i + 1, min(i + 4, len(words))):
                        next_word = words[j].strip(".,!?:;")
                        if len(next_word) > 2 and next_word not in ["the", "and", "or", "but", "is", "are"]:
                            emphasis_words.append(next_word)
                            break

    emphasis_words = list(dict.fromkeys(emphasis_words))[:3]

    emotions = []
    emotion_patterns = {
        "confident": ["confident", "certain", "sure", "definite"],
        "enthusiastic": ["excited", "thrilled", "amazing", "fantastic"],
        "cautious": ["careful", "consider", "might", "perhaps"],
        "urgent": ["urgent", "critical", "immediately", "must"],
    }
    for emotion, patterns in emotion_patterns.items():
        if any(pattern in normalized_notes for pattern in patterns):
            emotions.append(emotion)

    presentation_type = detect_presentation_type(normalized_notes, normalized_content)

    style_descriptions = {
        "professional": "Professional, authoritative, and structured delivery appropriate for business or academic settings.",
        "casual": "Friendly, conversational tone as if speaking to colleagues or friends.",
        "enthusiastic": "Energetic, passionate delivery that conveys excitement and engagement.",
        "technical": "Precise, methodical explanation with emphasis on accuracy and clarity.",
        "narrative": "Storytelling approach with natural flow and engaging rhythm.",
    }

    delivery_instructions = []
    if pace == "slow":
        delivery_instructions.append("Speak slowly and deliberately, allowing time for comprehension.")
    elif pace == "fast":
        delivery_instructions.append("Maintain a brisk but clear pace.")

    if emphasis_words:
        delivery_instructions.append(f"Give special emphasis to: {', '.join(emphasis_words)}")

    if emotions:
        delivery_instructions.append(f"Convey {emotions[0]} emotion in your delivery.")

    return {
        "tone": dominant_tone,
        "pace": pace,
        "emphasis_words": emphasis_words,
        "emotions": emotions,
        "presentation_type": presentation_type,
        "confidence_score": confidence_score,
        "style_description": style_descriptions.get(dominant_tone, style_descriptions["professional"]),
        "delivery_instructions": " ".join(delivery_instructions) if delivery_instructions else "Use clear, natural delivery.",
    }


def analyze_speaker_notes_to_style(speaker_notes: str, slide_content: str) -> str:
    """Convert speaker notes into style guideline text."""
    if not speaker_notes or not speaker_notes.strip():
        return get_default_professional_style()

    style_analysis = extract_style_indicators(speaker_notes, slide_content)

    return f"""SPEAKING STYLE ANALYSIS:

Detected Tone: {style_analysis['tone']}
Pace Indicators: {style_analysis['pace']}
Emphasis Points: {', '.join(style_analysis['emphasis_words']) if style_analysis['emphasis_words'] else 'None'}
Emotional Context: {', '.join(style_analysis['emotions']) if style_analysis['emotions'] else 'Neutral'}
Presentation Type: {style_analysis['presentation_type'].value}

STYLE GUIDELINES:
{style_analysis['style_description']}

DELIVERY INSTRUCTIONS:
{style_analysis['delivery_instructions']}"""


def create_fallback_prompt(style_guidelines: str, language_code: str) -> str:
    """Create fallback prompt when prompt rewriting fails."""
    lines = style_guidelines.split("\n")
    tone = "professional"
    pace = "normal"

    for line in lines:
        if "Detected Tone:" in line:
            tone = line.split(":", 1)[1].strip()
        elif "Pace Indicators:" in line:
            pace = line.split(":", 1)[1].strip()

    pace_instruction = ""
    if pace == "slow":
        pace_instruction = "Speak slowly and clearly. "
    elif pace == "fast":
        pace_instruction = "Speak at a brisk but clear pace. "

    tone_instruction = ""
    if tone == "enthusiastic":
        tone_instruction = "Use an energetic and passionate tone. "
    elif tone == "casual":
        tone_instruction = "Use a friendly, conversational tone. "
    elif tone == "technical":
        tone_instruction = "Use a precise, methodical delivery. "
    elif tone == "formal":
        tone_instruction = "Use a professional, authoritative tone. "

    language_label = "Chinese, Mandarin (China)" if language_code in {"yue-HK", "zh-HK", "yue"} else language_code
    cantonese_instruction = "使用香港廣東話輸出. " if language_code in {"yue-HK", "zh-HK", "yue"} else ""

    return (
        f"Speak in a {tone} manner appropriate for a presentation in {language_label}. \n"
        f"{cantonese_instruction}"
        f"{tone_instruction}{pace_instruction}Deliver the content with appropriate emphasis and natural flow for your audience."
    )


def create_concise_prompt(style_guidelines: str, language_code: str) -> str:
    """Create a concise prompt that stays within Gemini TTS limits."""
    lines = style_guidelines.split("\n")
    tone = "professional"
    pace = "normal"
    emphasis_words = []
    emotions = []

    for line in lines:
        if "Detected Tone:" in line:
            tone = line.split(":", 1)[1].strip()
        elif "Pace Indicators:" in line:
            pace = line.split(":", 1)[1].strip()
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

    language_label = "Chinese, Mandarin (China)" if language_code in {"yue-HK", "zh-HK", "yue"} else language_code
    components = [f"Speak in a {base_tone} manner"]

    if pace == "slow":
        components.append("at a slow, deliberate pace")
    elif pace == "fast":
        components.append("at a brisk pace")

    if emotions:
        components.append(f"with {emotions[0]} emotion")

    if emphasis_words:
        components.append(f"emphasizing {emphasis_words[0]}")

    prompt = ". ".join(components) + f" for {language_label}."
    if language_code in {"yue-HK", "zh-HK", "yue"}:
        prompt += " 使用香港廣東話輸出."
    if len(prompt) > 200:
        prompt = f"Speak in a {base_tone} manner for {language_label}."
        if language_code in {"yue-HK", "zh-HK", "yue"}:
            prompt += " 使用香港廣東話輸出."

    return prompt
