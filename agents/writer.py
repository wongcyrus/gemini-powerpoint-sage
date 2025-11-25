"""Speech Writer Agent."""

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from . import prompt

writer_agent = LlmAgent(
    name="speech_writer",
    model="gemini-2.5-flash", # Revert to Flash for stability
    description="A speech writer agent that generates presentation scripts with context.",
    instruction=prompt.WRITER_PROMPT,    
    tools=[google_search]
)
