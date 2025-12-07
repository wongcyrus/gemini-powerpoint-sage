"""Slide Analyst Agent."""

import os
from google.adk.agents import LlmAgent
from . import prompt

analyst_agent = LlmAgent(
    name="slide_analyst",
    model=os.getenv("MODEL_ANALYST", "gemini-1.5-pro"),
    description="A multimodal analyst that extracts insights from slide images.",
    instruction=prompt.ANALYST_PROMPT
)
