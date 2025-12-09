"""Application layer for Gemini PowerPoint Sage.

This layer handles CLI interface, command orchestration, and user interaction.
Business logic is delegated to the core services layer.
"""

from .cli import CLI
from .logging_setup import setup_logging

__all__ = ["CLI", "setup_logging"]
