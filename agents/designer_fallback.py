"""Fallback slide designer agent using latest Imagen model."""

import os

from google.adk.agents import LlmAgent

FALLBACK_DESIGNER_PROMPT = """
SYSTEM INSTRUCTION:
You generate a single presentation slide IMAGE (PNG/JPEG). Output ONLY image data.

TASK:
Create a clean, professional 16:9 slide based on provided speaker notes. Extract:
- A concise title (5-10 words)
- 3–4 short bullet points

STYLE:
- Balanced whitespace, readable typography, subtle modern color palette.
- No logos unless explicitly mentioned.
- Vector-style minimal shapes if needed (no photorealistic inventions).

Return ONLY the rendered slide image. Do not return text.
"""

fallback_designer_agent = LlmAgent(
    name="slide_designer_fallback",
    model=os.getenv("FALLBACK_IMAGEN_MODEL", "imagen-4.0-generate-001"),
    description="Fallback Imagen slide renderer",
    instruction=FALLBACK_DESIGNER_PROMPT,
)
