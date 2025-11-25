"""Image Translator Agent for Visual Localization."""

from google.adk.agents import LlmAgent
from . import prompt

image_translator_agent = LlmAgent(
    name="image_translator",
    model="gemini-3-pro-image-preview",
    description="Translates and localizes slide visuals for different languages while maintaining design consistency.",
    instruction=prompt.IMAGE_TRANSLATOR_PROMPT,
)
