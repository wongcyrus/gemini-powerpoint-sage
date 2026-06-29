"""Pure helper functions for presentation processing."""

from __future__ import annotations

import re
from typing import Callable


LANGUAGE_NAME_MAP = {
    "en": "English",
    "zh-CN": "Simplified Chinese (简体中文)",
    "zh-TW": "Traditional Chinese (繁體中文)",
    "yue-HK": "Cantonese (廣東話)",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "de": "German (Deutsch)",
    "it": "Italian (Italiano)",
    "pt": "Portuguese (Português)",
    "ru": "Russian (Русский)",
    "ar": "Arabic (العربية)",
    "hi": "Hindi (हिन्दी)",
    "th": "Thai (ไทย)",
    "vi": "Vietnamese (Tiếng Việt)",
}


def get_language_name(language_code: str) -> str:
    """Map a locale to the label used in prompts."""
    return LANGUAGE_NAME_MAP.get(language_code, language_code)


def is_error_response(response: str) -> bool:
    """Detect tool-style error responses without matching normal prose."""
    if not response or not response.strip():
        return False

    response_stripped = response.strip()
    response_lower = response_stripped.lower()

    if (
        response_lower.startswith("system_error:")
        or response_lower.startswith("tool_error:")
        or response_lower.startswith("processing_error:")
    ):
        return True

    specific_tool_errors = [
        "error: the writer agent failed to generate a script",
        "error: the analyst agent failed",
        "error: the translator agent failed",
        "error: the auditor agent failed",
        "error: the designer agent failed",
        "please try again or use a placeholder",
        "failed to generate a script",
        "tool execution failed",
        "agent returned empty",
    ]

    for error_msg in specific_tool_errors:
        if error_msg in response_lower:
            return True

    error_starters = [
        "error:",
        "failed:",
        "cannot generate",
        "unable to generate",
        "generation failed",
        "workflow failed:",
    ]

    for starter in error_starters:
        if response_lower.startswith(starter):
            return True

    if len(response_stripped) < 30 and len(response_stripped.split()) < 6:
        obvious_errors = ["error", "failed", "timeout", "exception"]
        if any(response_lower.startswith(word) for word in obvious_errors):
            return True

    return False


def build_supervisor_prompt(
    slide_idx: int,
    image_id: str,
    existing_notes: str,
    previous_slide_summary: str,
    presentation_theme: str,
    global_context: str,
    target_language: str,
    total_slides: int | None = None,
    previous_speaker_notes: list | None = None,
) -> str:
    """Build the supervisor prompt from primitive values."""
    slide_position_info = ""
    if total_slides:
        if slide_idx == 1:
            slide_position_info = (
                f"SLIDE POSITION: This is the FIRST slide (slide {slide_idx} of {total_slides}). "
                "Include appropriate greeting.\n"
            )
        elif slide_idx == total_slides:
            slide_position_info = (
                f"SLIDE POSITION: This is the LAST slide (slide {slide_idx} of {total_slides}). "
                "Include appropriate closing.\n"
            )
        else:
            slide_position_info = (
                f"SLIDE POSITION: This is a MIDDLE slide (slide {slide_idx} of {total_slides}). "
                "NO greetings or farewells.\n"
            )

    previous_notes_context = ""
    if previous_speaker_notes:
        previous_notes_context = "PREVIOUS_SPEAKER_NOTES:\n"
        for note_data in previous_speaker_notes[-3:]:
            previous_notes_context += f"Slide {note_data['slide_idx']}: {note_data['notes']}\n"
        previous_notes_context += "\n"

    return (
        f"Here is Slide {slide_idx}.\n"
        f"Existing Notes: \"{existing_notes}\"\n"
        f"Image ID: \"{image_id}\"\n"
        f"Previous Slide Summary: \"{previous_slide_summary}\"\n"
        f"{previous_notes_context}"
        f"Theme: \"{presentation_theme}\"\n"
        f"Global Context: \"{global_context}\"\n"
        f"{slide_position_info}"
        f"TARGET_LANGUAGE: {target_language}\n\n"
        f"Please proceed with the workflow."
    )


def extract_video_prompt(speaker_notes: str) -> str:
    """Derive a concise video prompt from slide speaker notes."""
    if not speaker_notes or not speaker_notes.strip():
        return "Create an engaging visual representation of key concepts."

    lines = speaker_notes.strip().split("\n")
    first_line = lines[0] if lines else speaker_notes

    if len(first_line) > 150:
        first_line = first_line[:150].rsplit(" ", 1)[0] + "."

    return (
        "Create a professional 8-10 second video that visually "
        f"illustrates this concept: {first_line} "
        "Use modern design, clear visuals, and professional animation. "
        "Focus on clarity and visual appeal."
    )


def extract_artifact_id(agent_response: str) -> str:
    """Extract a video artifact reference from an agent response."""
    if not agent_response:
        return ""

    match = re.search(
        r'artifact[_-]?id["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
        agent_response,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)

    match = re.search(r"(video[_\w]*\.mp4)", agent_response, re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r"(video[_\w]*)", agent_response, re.IGNORECASE)
    if match:
        return match.group(1)

    return ""


def build_global_context_translation_prompt(
    en_global_context: str,
    lang_name: str,
    language_code: str,
) -> str:
    """Build the translation prompt used for cached global context."""
    chinese_instruction = ""
    if language_code == "zh-CN":
        chinese_instruction = (
            "\n\nCHINESE LOCALE REQUIREMENT: "
            "You MUST use ONLY Simplified Chinese characters (简体中文). "
            "Examples: Use 网络 (not 網絡), 数据 (not 數據), 计算机 (not 計算機)."
        )
    elif language_code in ["zh-TW", "zh-HK", "yue-HK"]:
        chinese_instruction = (
            "\n\nCHINESE LOCALE REQUIREMENT: "
            "You MUST use ONLY Traditional Chinese characters (繁體中文). "
            "Examples: Use 網絡 (not 网络), 數據 (not 数据), 計算機 (not 计算机)."
        )

    return (
        f"Translate the following presentation overview to {lang_name}. "
        f"Apply the configured speaker style and adapt cultural references appropriately. "
        f"Maintain the narrative structure and key vocabulary while ensuring the content "
        f"sounds natural and engaging in {lang_name}.\n\n"
        f"PRESENTATION OVERVIEW:\n{en_global_context}\n\n"
        f"IMPORTANT: Provide ONLY the translated overview in {lang_name}. "
        f"Do not include explanations or metadata.{chinese_instruction}"
    )


def build_visual_translation_prompt(lang_name: str, speaker_notes: str) -> str:
    """Build the prompt used to translate an existing English slide visual."""
    return (
        f"Translate this English slide visual to {lang_name}. \n\n"
        f"IMPORTANT:\n"
        f"- Translate ALL text to {lang_name}\n"
        f"- Keep the exact same layout and structure\n"
        f"- Ensure text is readable and fits within the original text areas\n"
        f"- Do NOT change colors, fonts, or design\n"
        f"- Do NOT add or remove elements\n\n"
        f"Speaker Notes: {speaker_notes}"
    )


def build_global_context_generation_prompt(total_slides: int) -> str:
    """Build the prompt used to generate a new global context."""
    return (
        "Here are the slides for the entire presentation. Analyze them. "
        f"Note: This presentation has exactly {total_slides} slides."
    )


def build_english_visuals_dir(output_dir: str, pptx_path: str) -> str:
    """Build the path to the English visuals directory.

    Accept either the presentation output root or a language-specific visuals
    directory and normalize to the sibling English directory.
    """
    import os

    pptx_base = os.path.splitext(os.path.basename(pptx_path))[0]
    english_dir_name = f"{pptx_base}_en_visuals"
    base_name = os.path.basename(os.path.normpath(output_dir))

    if base_name == english_dir_name:
        return output_dir

    if base_name.startswith(f"{pptx_base}_") and base_name.endswith("_visuals"):
        return os.path.join(os.path.dirname(output_dir), english_dir_name)

    return os.path.join(output_dir, english_dir_name)


async def process_slide_visual(
    *,
    slide_idx: int,
    slide_visuals,
    slide_image,
    speaker_notes: str,
    status: str,
    language: str,
    visuals_dir: str,
    pptx_path: str,
    retry_errors: bool,
    image_translator_agent,
    visual_generator,
    replace_visual: Callable[..., object],
    run_visual_agent: Callable[..., object],
    get_language_name: Callable[[str], str],
) -> int:
    """Process a single slide's visual branch and return 1 if missing."""
    import os
    from PIL import Image

    if status != "success":
        return 1

    translated = False
    if language != "en" and image_translator_agent:
        english_visuals_dir = build_english_visuals_dir(visuals_dir, pptx_path)
        target_img_path = os.path.join(visuals_dir, f"slide_{slide_idx}_reimagined.png")
        en_img_path = os.path.join(english_visuals_dir, f"slide_{slide_idx}_reimagined.png")

        if os.path.exists(target_img_path) and not retry_errors:
            replace_visual(slide_visuals, target_img_path, speaker_notes)
            translated = True
        elif os.path.exists(en_img_path):
            english_visual = Image.open(en_img_path)
            lang_name = get_language_name(language)
            design_prompt = (
                f"Translate this English slide visual to {lang_name}. \n\n"
                f"IMPORTANT:\n"
                f"- Translate ALL text to {lang_name}\n"
                f"- Keep the exact same layout and structure\n"
                f"- Ensure text is readable and fits within the original text areas\n"
                f"- Do NOT change colors, fonts, or design\n"
                f"- Do NOT add or remove elements\n\n"
                f"Speaker Notes: {speaker_notes}"
            )
            img_bytes = await run_visual_agent(
                image_translator_agent,
                design_prompt,
                images=[english_visual],
            )
            if img_bytes:
                os.makedirs(visuals_dir, exist_ok=True)
                with open(target_img_path, "wb") as f:
                    f.write(img_bytes)
                replace_visual(slide_visuals, target_img_path, speaker_notes)
                translated = True

    if not translated:
        img_bytes = await visual_generator.generate_visual(
            slide_idx,
            slide_image,
            speaker_notes,
            retry_errors,
            language,
        )
        if img_bytes:
            replace_visual(
                slide_visuals,
                os.path.join(visuals_dir, f"slide_{slide_idx}_reimagined.png"),
                speaker_notes,
            )
        else:
            return 1

    return 0
