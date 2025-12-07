"""Speech Writer Agent."""

import os
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from . import prompt

writer_agent = LlmAgent(
    name="speech_writer",
    model=os.getenv("MODEL_WRITER", "gemini-1.5-flash"),
    description="A speech writer agent that generates presentation scripts with context.",
    instruction=prompt.WRITER_PROMPT,    
    tools=[google_search]
)
