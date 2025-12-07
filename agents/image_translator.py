"""Image Translator Agent for Visual Localization."""

import os
from google.adk.agents import LlmAgent
from . import prompt

image_translator_agent = LlmAgent(
    name="image_translator",
    model=os.getenv("MODEL_IMAGE_TRANSLATOR", "gemini-2.5-flash"),
    description="Translates and localizes slide visuals for different languages while maintaining design consistency.",
    instruction=prompt.IMAGE_TRANSLATOR_PROMPT,
)
