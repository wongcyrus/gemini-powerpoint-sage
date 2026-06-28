"""Pure helpers for video prompt construction and parsing."""

from __future__ import annotations

import re


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
