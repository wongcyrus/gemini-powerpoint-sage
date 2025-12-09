"""Presentation storage abstraction."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from core.domain import Presentation


class PresentationStorage(ABC):
    """Abstract interface for presentation storage operations."""
    
    @abstractmethod
    def load(self, pptx_path: Path, pdf_path: Path) -> Presentation:
        """
        Load a presentation from files.
        
        Args:
            pptx_path: Path to PowerPoint file
            pdf_path: Path to PDF file
            
        Returns:
            Presentation entity
        """
        pass
    
    @abstractmethod
    def save(self, presentation: Presentation, output_path: Path) -> None:
        """
        Save a presentation to file.
        
        Args:
            presentation: Presentation entity to save
            output_path: Path where to save the presentation
        """
        pass
    
    @abstractmethod
    def extract_slides(self, presentation: Presentation) -> None:
        """
        Extract slides from presentation files.
        
        Args:
            presentation: Presentation entity to populate with slides
        """
        pass
    
    @abstractmethod
    def update_speaker_notes(
        self,
        presentation: Presentation,
        output_path: Path
    ) -> None:
        """
        Update speaker notes in presentation file.
        
        Args:
            presentation: Presentation with updated notes
            output_path: Path where to save updated presentation
        """
        pass
