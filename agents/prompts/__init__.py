"""Agent prompts for Gemini Powerpoint Sage."""

from .supervisor import SUPERVISOR_PROMPT
from .analyst import ANALYST_PROMPT
from .writer import WRITER_PROMPT
from .auditor import AUDITOR_PROMPT
from .overviewer import OVERVIEWER_PROMPT
from .designer import DESIGNER_PROMPT
from .translator import TRANSLATOR_PROMPT
from .image_translator import IMAGE_TRANSLATOR_PROMPT
from .video_generator import VIDEO_GENERATOR_PROMPT
from .title_generator import TITLE_GENERATOR_PROMPT
from .refiner import REFINER_PROMPT

__all__ = [
    "SUPERVISOR_PROMPT",
    "ANALYST_PROMPT",
    "WRITER_PROMPT",
    "AUDITOR_PROMPT",
    "OVERVIEWER_PROMPT",
    "DESIGNER_PROMPT",
    "TRANSLATOR_PROMPT",
    "IMAGE_TRANSLATOR_PROMPT",
    "VIDEO_GENERATOR_PROMPT",
    "TITLE_GENERATOR_PROMPT",
    "REFINER_PROMPT",
]
