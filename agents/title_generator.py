"""Title Generator Agent for creating compelling slide titles."""

import os
from google.adk.agents import LlmAgent
from . import prompt

title_generator_agent = LlmAgent(
    name="title_generator",
    model=os.getenv("MODEL_TITLE_GENERATOR", "gemini-2.5-flash"),
    description="Generates short, catchy titles for presentation slides based on content and speaker style.",
    instruction=prompt.TITLE_GENERATOR_PROMPT,
)
