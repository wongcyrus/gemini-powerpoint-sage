"""Slide Designer Agent."""

import os
from google.adk.agents import LlmAgent
from . import prompt

designer_agent = LlmAgent(
    name="slide_designer",
    model=os.getenv("MODEL_DESIGNER", "gemini-1.5-pro"),
    description="Generates high-fidelity slide images.",
    instruction=prompt.DESIGNER_PROMPT
)
