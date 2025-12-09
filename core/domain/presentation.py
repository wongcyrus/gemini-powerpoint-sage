"""Presentation domain entity."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
from .slide import Slide


@dataclass
class Presentation:
    """Presentation entity representing a PowerPoint deck."""
    
    pptx_path: Path
    pdf_path: Path
    slides: List[Slide] = field(default_factory=list)
    language: str = "en"
    style: Optional[str] = None
    course_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate presentation."""
        if not isinstance(self.pptx_path, Path):
            self.pptx_path = Path(self.pptx_path)
        
        if not isinstance(self.pdf_path, Path):
            self.pdf_path = Path(self.pdf_path)
        
        if not self.pptx_path.exists():
            raise ValueError(f"PPTX file not found: {self.pptx_path}")
        
        if not self.pdf_path.exists():
            raise ValueError(f"PDF file not found: {self.pdf_path}")
    
    def add_slide(self, slide: Slide) -> None:
        """Add a slide to the presentation."""
        if not isinstance(slide, Slide):
            raise TypeError("Must add a Slide instance")
        self.slides.append(slide)
    
    def get_slide(self, index: int) -> Optional[Slide]:
        """Get slide by index."""
        for slide in self.slides:
            if slide.index == index:
                return slide
        return None
    
    def get_slides_needing_processing(self) -> List[Slide]:
        """Get all slides that need processing."""
        return [slide for slide in self.slides if slide.needs_processing()]
    
    def get_slides_with_errors(self) -> List[Slide]:
        """Get all slides with errors."""
        return [slide for slide in self.slides if slide.has_error]
    
    def total_slides(self) -> int:
        """Get total number of slides."""
        return len(self.slides)
    
    def processed_slides(self) -> int:
        """Get number of processed slides."""
        return sum(1 for slide in self.slides if slide.has_useful_notes())
    
    def progress_percentage(self) -> float:
        """Get processing progress percentage."""
        if not self.slides:
            return 0.0
        return (self.processed_slides() / self.total_slides()) * 100
    
    def is_complete(self) -> bool:
        """Check if all slides are processed."""
        return all(slide.has_useful_notes() for slide in self.slides)
    
    def get_output_path(self, suffix: str = "_notes") -> Path:
        """Get output path for processed presentation."""
        stem = self.pptx_path.stem
        parent = self.pptx_path.parent
        ext = self.pptx_path.suffix
        
        # Add language suffix if not English
        if self.language != "en":
            return parent / f"{stem}_{self.language}{suffix}{ext}"
        return parent / f"{stem}{suffix}{ext}"
    
    def __str__(self) -> str:
        """Return string representation."""
        return f"Presentation: {self.pptx_path.name} ({self.total_slides()} slides)"
    
    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"Presentation(pptx_path={self.pptx_path}, "
            f"slides={self.total_slides()}, "
            f"language={self.language}, "
            f"progress={self.progress_percentage():.1f}%)"
        )
