"""Presentation Overviewer Agent."""

from google.adk.agents import LlmAgent
from . import prompt

overviewer_agent = LlmAgent(
    name="presentation_overviewer",
    model="gemini-3-pro-preview", # Use gemini-3-pro-preview for high quality overview
    description="Analyzes the entire slide deck to establish global context and narrative flow.",
    instruction=prompt.OVERVIEWER_PROMPT
)
