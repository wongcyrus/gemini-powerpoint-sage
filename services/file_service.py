"""File operations service."""

import logging
import os
import shutil
import tempfile
from typing import Optional

import pymupdf
from pptx import Presentation
from pptx.util import Inches

from config.constants import SlideConfig
from utils.error_handling import ProcessingError

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations."""
    
    @staticmethod
    def load_presentation(pptx_path: str) -> Presentation:
        """
        Load PowerPoint presentation.
        
        Args:
            pptx_path: Path to PPTX file
            
        Returns:
            Presentation object
            
        Raises:
            ProcessingError: If file cannot be loaded
        """
        try:
            return Presentation(pptx_path)
        except Exception as e:
            raise ProcessingError(f"Failed to load PPTX: {e}") from e
    
    @staticmethod
    def load_pdf(pdf_path: str):
        """
        Load PDF document.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            PDF document object
            
        Raises:
            ProcessingError: If file cannot be loaded
        """
        try:
            return pymupdf.open(pdf_path)
        except Exception as e:
            raise ProcessingError(f"Failed to load PDF: {e}") from e
    
    @staticmethod
    def save_presentation(
        prs: Presentation,
        output_path: str,
        source_path: Optional[str] = None,
        force_aspect_ratio: bool = False,
    ) -> str:
        """
        Save PowerPoint presentation.
        
        Args:
            prs: Presentation object
            output_path: Path to save to
            source_path: Optional source path for VBA restoration
            force_aspect_ratio: Whether to force 16:9 aspect ratio
            
        Returns:
            Path to saved file
            
        Raises:
            ProcessingError: If save fails
        """
        try:
            # Force aspect ratio if requested
            if force_aspect_ratio:
                prs.slide_width = Inches(SlideConfig.SLIDE_WIDTH_INCHES)
                prs.slide_height = Inches(SlideConfig.SLIDE_HEIGHT_INCHES)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to temporary file first
            from utils.pptx_utils import ensure_pptx_path
            temp_path = ensure_pptx_path(output_path)
            prs.save(temp_path)
            
            logger.info(f"Saved presentation (intermediate) to: {temp_path}")
            
            # Restore VBA if needed
            if source_path and FileService._needs_vba_restoration(
                source_path, output_path
            ):
                from utils.pptx_utils import restore_vba_project
                restore_vba_project(source_path, temp_path, output_path)
                logger.info(f"Saved presentation with VBA to: {output_path}")
            else:
                # Move to final location
                if temp_path != output_path:
                    shutil.move(temp_path, output_path)
                logger.info(f"Saved presentation to: {output_path}")
            
            return output_path
            
        except Exception as e:
            raise ProcessingError(f"Failed to save PPTX: {e}") from e
    
    @staticmethod
    def _needs_vba_restoration(source_path: str, output_path: str) -> bool:
        """Check if VBA restoration is needed."""
        src_ext = os.path.splitext(source_path)[1].lower()
        out_ext = os.path.splitext(output_path)[1].lower()
        return src_ext == ".pptm" and out_ext == ".pptm"
    
    @staticmethod
    def validate_files(pptx_path: str, pdf_path: str) -> None:
        """
        Validate that required files exist.
        
        Args:
            pptx_path: Path to PPTX file
            pdf_path: Path to PDF file
            
        Raises:
            ProcessingError: If files don't exist
        """
        if not os.path.exists(pptx_path):
            raise ProcessingError(f"PPTX file not found: {pptx_path}")
        
        if not os.path.exists(pdf_path):
            raise ProcessingError(f"PDF file not found: {pdf_path}")
    
    @staticmethod
    def get_slide_count(pptx_path: str, pdf_path: str) -> int:
        """
        Get the number of slides to process.
        
        Args:
            pptx_path: Path to PPTX file
            pdf_path: Path to PDF file
            
        Returns:
            Number of slides (minimum of PPTX and PDF)
        """
        prs = FileService.load_presentation(pptx_path)
        pdf_doc = FileService.load_pdf(pdf_path)
        
        count = min(len(prs.slides), len(pdf_doc))
        
        pdf_doc.close()
        
        return count
    
    @staticmethod
    def create_output_directory(path: str) -> None:
        """
        Create output directory if it doesn't exist.
        
        Args:
            path: Directory path
        """
        os.makedirs(path, exist_ok=True)


from typing import Optional
