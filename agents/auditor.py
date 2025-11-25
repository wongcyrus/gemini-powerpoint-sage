"""Note Auditor Agent."""

from google.adk.agents import LlmAgent
from . import prompt

auditor_agent = LlmAgent(
    name="note_auditor",
    model="gemini-2.5-flash",
    description="A quality control agent that evaluates existing speaker notes.",
    instruction=prompt.AUDITOR_PROMPT
)
