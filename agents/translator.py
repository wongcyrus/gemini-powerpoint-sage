"""Translator Agent for Multi-Language Support."""

from google.adk.agents import LlmAgent
from . import prompt

translator_agent = LlmAgent(
    name="translator",
    model="gemini-2.5-flash",
    description="Translates speaker notes and slide text to target languages with cultural adaptation.",
    instruction=prompt.TRANSLATOR_PROMPT,
)
