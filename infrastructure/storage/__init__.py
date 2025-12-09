"""Storage abstractions for file operations."""

from .presentation_storage import PresentationStorage
from .progress_storage import ProgressStorage

__all__ = ["PresentationStorage", "ProgressStorage"]
