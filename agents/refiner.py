"""Refiner Agent."""

from google.adk.agents import LlmAgent
from . import prompt

refiner_agent = LlmAgent(
    name="speech_refiner",
    model="gemini-2.5-flash",
    description="A speech refinement agent that optimizes text for TTS.",
    instruction=prompt.REFINER_PROMPT,
)
