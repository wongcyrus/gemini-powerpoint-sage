"""Note Auditor Agent."""

import os
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from . import prompt

auditor_agent = LlmAgent(
    name="note_auditor",
    model=os.getenv("MODEL_AUDITOR", "gemini-2.5-flash"),
    description="A quality control agent that evaluates existing speaker notes.",
    instruction=prompt.AUDITOR_PROMPT,
    tools=[google_search]
)
