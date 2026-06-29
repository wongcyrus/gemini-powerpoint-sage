"""Pure helpers for video prompt construction and parsing."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List


def build_video_prompt(speaker_notes: str) -> str:
    """Build a concise video prompt from speaker notes."""
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


def build_video_agent_prompt(video_prompt: str, speaker_notes: str) -> str:
    """Build the prompt sent to the video generation agent."""
    return (
        "Generate a professional video for a presentation "
        f"slide based on this concept:\n\n{video_prompt}\n\n"
        f"Speaker Notes:\n{speaker_notes}\n\n"
        "Generate an 8-10 second video."
    )


def build_veo_video_prompt(
    *,
    slide_idx: int,
    role: str,
    video_prompt: str,
    speaker_notes: str,
    presentation_theme: str,
    global_context: str,
    language: str,
) -> str:
    """Build the prompt sent to Veo for a specific planned moment."""
    return (
        f"Create a short presentation video for slide {slide_idx}.\n"
        f"Role: {role}\n"
        f"Concept: {video_prompt}\n"
        f"Speaker notes: {speaker_notes}\n"
        f"Presentation theme: {presentation_theme}\n"
        f"Global context: {global_context}\n"
        f"Language: {language}\n\n"
        "Keep the clip cinematic, polished, and faithful to the slide content. "
        "Use the slide image as the visual reference and make the motion feel "
        "natural, professional, and presentation-friendly."
    )


def _slide_summary_text(slide_data: Dict[str, Any]) -> str:
    notes = (slide_data.get("speaker_notes") or "").strip()
    if not notes:
        return "No speaker notes available."
    summary = notes.split("\n", 1)[0].strip()
    if len(summary) > 180:
        summary = summary[:180].rsplit(" ", 1)[0].strip()
    return summary


def build_video_planner_prompt(
    slide_data: List[Dict[str, Any]],
    presentation_theme: str,
    global_context: str,
    language: str,
    max_clips: int = 3,
) -> str:
    """Build the prompt used to ask the model which moments deserve video."""
    slide_lines = []
    for slide in slide_data:
        slide_lines.append(
            f"- Slide {slide['slide_idx']}: {_slide_summary_text(slide)}"
        )

    return (
        "You are a presentation video planner.\n\n"
        "TASK:\n"
        f"Choose at most {max_clips} moments in the deck that deserve a separate "
        "video treatment. Prefer intro, section-change, and conclusion moments. "
        "Do NOT choose every slide.\n\n"
        "RULES:\n"
        f"- Return JSON only.\n"
        f"- If no strong video moment exists, return an empty list.\n"
        f"- Keep the original slide deck unchanged.\n"
        f"- Never create a new slide.\n"
        f"- Focus on high-value moments only.\n\n"
        "OUTPUT SCHEMA:\n"
        "{\n"
        '  "should_generate": true,\n'
        '  "moments": [\n'
        '    {\n'
        '      "slide_idx": 1,\n'
        '      "role": "intro|section|conclusion",\n'
        '      "reason": "why this moment deserves video",\n'
        '      "prompt": "short sidecar video concept"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"PRESENTATION THEME: {presentation_theme}\n"
        f"GLOBAL CONTEXT: {global_context}\n"
        f"LANGUAGE: {language}\n"
        "SLIDES:\n"
        + "\n".join(slide_lines)
    )


def parse_video_plan_response(agent_response: str, max_clips: int = 3) -> Dict[str, Any]:
    """Parse a JSON planning response into a normalized plan dictionary."""
    raw = (agent_response or "").strip()
    if not raw:
        return {"should_generate": False, "moments": [], "source": "empty"}

    candidates = [raw]
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.insert(0, fenced.group(1))
    else:
        generic = re.search(r"(\{.*\})", raw, re.DOTALL)
        if generic:
            candidates.insert(0, generic.group(1))

    parsed: Dict[str, Any] | None = None
    for candidate in candidates:
        try:
            loaded = json.loads(candidate)
            if isinstance(loaded, dict):
                parsed = loaded
                break
        except json.JSONDecodeError:
            continue

    if not parsed:
        return {"should_generate": False, "moments": [], "source": "unparsed"}

    moments = []
    seen = set()
    for item in parsed.get("moments", [])[:max_clips]:
        if not isinstance(item, dict):
            continue
        slide_idx = item.get("slide_idx")
        try:
            slide_idx = int(slide_idx)
        except (TypeError, ValueError):
            continue
        if slide_idx in seen:
            continue
        seen.add(slide_idx)
        moments.append(
            {
                "slide_idx": slide_idx,
                "role": str(item.get("role", "section")),
                "reason": str(item.get("reason", "")).strip(),
                "prompt": str(item.get("prompt", "")).strip(),
            }
        )

    return {
        "should_generate": bool(parsed.get("should_generate", bool(moments))),
        "moments": moments,
        "source": "ai",
    }


def build_fallback_video_plan(
    slide_data: List[Dict[str, Any]],
    presentation_theme: str,
    global_context: str,
    language: str,
    max_clips: int = 3,
) -> Dict[str, Any]:
    """Build a deterministic fallback plan when no model plan is available."""
    slides = [item for item in slide_data if item.get("status") == "success"]
    if not slides:
        return {
            "should_generate": False,
            "moments": [],
            "source": "fallback",
            "presentation_theme": presentation_theme,
            "global_context": global_context,
            "language": language,
        }

    selected = []

    first = slides[0]
    selected.append(
        {
            "slide_idx": first["slide_idx"],
            "role": "intro",
            "reason": "Opening hook for the presentation.",
            "prompt": _slide_summary_text(first),
        }
    )

    if len(slides) > 2 and len(selected) < max_clips:
        middle = slides[len(slides) // 2]
        if middle["slide_idx"] not in {selected[0]["slide_idx"]}:
            selected.append(
                {
                    "slide_idx": middle["slide_idx"],
                    "role": "section",
                    "reason": "Representative section transition or main concept.",
                    "prompt": _slide_summary_text(middle),
                }
            )

    if len(slides) > 1 and len(selected) < max_clips:
        last = slides[-1]
        if last["slide_idx"] not in {item["slide_idx"] for item in selected}:
            selected.append(
                {
                    "slide_idx": last["slide_idx"],
                    "role": "conclusion",
                    "reason": "Closing summary or call to action.",
                    "prompt": _slide_summary_text(last),
                }
            )

    return {
        "should_generate": bool(selected),
        "moments": selected[:max_clips],
        "source": "fallback",
        "presentation_theme": presentation_theme,
        "global_context": global_context,
        "language": language,
    }


def extract_artifact_id(agent_response: str) -> str:
    """Extract a video artifact reference from agent response text."""
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


def format_video_prompt_file(
    slide_idx: int,
    video_prompt: str,
    speaker_notes: str,
    video_artifact: str | None = None,
) -> str:
    """Render the content written to a video prompt file."""
    content = [
        f"Slide {slide_idx} Video Prompt",
        "=" * 29,
        "",
        f"Prompt:\n{video_prompt}",
        "",
        f"Speaker Notes:\n{speaker_notes}",
    ]
    if video_artifact:
        content.extend(["", f"Generated Video: {video_artifact}"])
    return "\n".join(content) + "\n"
