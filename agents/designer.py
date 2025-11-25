"""Slide Designer Agent."""

from google.adk.agents import LlmAgent
from . import prompt

designer_agent = LlmAgent(
    name="slide_designer",
    model="gemini-3-pro-image-preview",
    description="Generates high-fidelity slide images.",
    instruction=prompt.DESIGNER_PROMPT
)
