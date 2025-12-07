"""Presentation Overviewer Agent."""

import os
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from . import prompt

overviewer_agent = LlmAgent(
    name="presentation_overviewer",
    model=os.getenv("MODEL_OVERVIEWER", "gemini-2.5-flash"),
    description="Analyzes the entire slide deck to establish global context and narrative flow.",
    instruction=prompt.OVERVIEWER_PROMPT,
    tools=[google_search]
)
