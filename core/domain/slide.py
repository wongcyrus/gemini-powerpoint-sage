"""Slide domain entities."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .notes import SpeakerNotes


@dataclass
class SlideContent:
    """Content extracted from a slide."""
    
    topic: str
    details: str
    visuals: str
    intent: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "topic": self.topic,
            "details": self.details,
            "visuals": self.visuals,
            "intent": self.intent,
        }


@dataclass
class Slide:
    """Presentation slide entity."""
    
    index: int
    title: Optional[str] = None
    notes: Optional[SpeakerNotes] = None
    content: Optional[SlideContent] = None
    image_path: Optional[str] = None
    has_error: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate slide."""
        if self.index < 0:
            raise ValueError("Slide index must be non-negative")
    
    def has_notes(self) -> bool:
        """Check if slide has speaker notes."""
        return self.notes is not None and not self.notes.is_empty()
    
    def has_useful_notes(self) -> bool:
        """Check if slide has useful speaker notes."""
        return self.has_notes() and self.notes.is_useful
    
    def needs_processing(self) -> bool:
        """Check if slide needs processing."""
        return not self.has_useful_notes() or (self.notes and self.notes.needs_regeneration)
    
    def mark_error(self, error_message: str) -> None:
        """Mark slide as having an error."""
        self.has_error = True
        self.error_message = error_message
    
    def clear_error(self) -> None:
        """Clear error status."""
        self.has_error = False
        self.error_message = None
    
    def set_notes(self, text: str, language: str = "en") -> None:
        """Set speaker notes for this slide."""
        self.notes = SpeakerNotes(text=text, language=language)
    
    def set_content(self, topic: str, details: str, visuals: str, intent: str) -> None:
        """Set analyzed content for this slide."""
        self.content = SlideContent(
            topic=topic,
            details=details,
            visuals=visuals,
            intent=intent
        )
    
    def __str__(self) -> str:
        """Return string representation."""
        return f"Slide {self.index}: {self.title or 'Untitled'}"
