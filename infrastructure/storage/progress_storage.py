"""Progress storage abstraction."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from core.domain import Presentation


class ProgressStorage(ABC):
    """Abstract interface for progress tracking storage."""
    
    @abstractmethod
    def load_progress(self, presentation: Presentation) -> Dict[str, Any]:
        """
        Load processing progress for a presentation.
        
        Args:
            presentation: Presentation entity
            
        Returns:
            Progress data dictionary
        """
        pass
    
    @abstractmethod
    def save_progress(
        self,
        presentation: Presentation,
        progress_data: Dict[str, Any]
    ) -> None:
        """
        Save processing progress for a presentation.
        
        Args:
            presentation: Presentation entity
            progress_data: Progress data to save
        """
        pass
    
    @abstractmethod
    def get_progress_path(self, presentation: Presentation) -> Path:
        """
        Get the path where progress is stored.
        
        Args:
            presentation: Presentation entity
            
        Returns:
            Path to progress file
        """
        pass
    
    @abstractmethod
    def clear_progress(self, presentation: Presentation) -> None:
        """
        Clear progress for a presentation.
        
        Args:
            presentation: Presentation entity
        """
        pass
