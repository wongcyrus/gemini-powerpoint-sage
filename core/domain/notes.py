"""Speaker notes domain entity."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SpeakerNotes:
    """Speaker notes for a slide."""
    
    text: str
    language: str = "en"
    is_useful: bool = True
    needs_regeneration: bool = False
    
    def __post_init__(self):
        """Validate speaker notes."""
        if not isinstance(self.text, str):
            raise ValueError("Speaker notes text must be a string")
        
        if not self.language:
            raise ValueError("Language must be specified")
    
    def is_empty(self) -> bool:
        """Check if notes are empty."""
        return not self.text or not self.text.strip()
    
    def mark_for_regeneration(self) -> None:
        """Mark notes as needing regeneration."""
        self.needs_regeneration = True
        self.is_useful = False
    
    def mark_as_useful(self) -> None:
        """Mark notes as useful."""
        self.is_useful = True
        self.needs_regeneration = False
    
    def __len__(self) -> int:
        """Return length of notes text."""
        return len(self.text)
    
    def __str__(self) -> str:
        """Return string representation."""
        return self.text
