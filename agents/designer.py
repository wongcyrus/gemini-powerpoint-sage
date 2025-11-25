"""Slide Designer Agent."""

from google.adk.agents import LlmAgent
from . import prompt

designer_agent = LlmAgent(
    name="slide_designer",
    model="gemini-3-pro-image-preview", # Specialized for image generation
    description="Generates high-fidelity slide images based on drafts and notes.",
    instruction=prompt.DESIGNER_PROMPT
)
