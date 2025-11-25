"""Slide Analyst Agent."""

from google.adk.agents import LlmAgent
from . import prompt

analyst_agent = LlmAgent(
    name="slide_analyst",
    model="gemini-3-pro-preview", # Use gemini-3-pro-preview for detailed multimodal analysis
    description="A multimodal analyst that extracts insights from slide images.",
    instruction=prompt.ANALYST_PROMPT
)
