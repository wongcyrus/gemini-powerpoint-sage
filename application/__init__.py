"""Application layer for Gemini PowerPoint Sage.

This layer handles CLI interface, unified processing, and user interaction.
Business logic is delegated to the core services layer.
"""

from dotenv import find_dotenv, load_dotenv

_dotenv_path = find_dotenv(usecwd=True)
if _dotenv_path:
    load_dotenv(_dotenv_path)

from .cli import CLI
from .logging_setup import setup_logging
from .unified_processor import UnifiedProcessor
from .input_scanner import InputScanner

__all__ = ["CLI", "setup_logging", "UnifiedProcessor", "InputScanner"]
