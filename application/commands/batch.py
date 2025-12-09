"""Batch command for processing multiple presentations."""

import logging
import os
import sys
from typing import List, Optional

from .base import Command
from .process import ProcessCommand

logger = logging.getLogger(__name__)


class BatchCommand(Command):
    """Command to process all presentations in a folder."""
    
    def __init__(
        self,
        folder_path: str,
        course_id: Optional[str] = None,
        retry_errors: bool = False,
        region: str = "global",
        skip_visuals: bool = False,
        generate_videos: bool = False,
        languages: str = "en",
        style: Optional[str] = None,
    ):
        """
        Initialize batch command.
        
        Args:
            folder_path: Path to folder containing PPTX files
            course_id: Optional course ID for context
            retry_errors: Whether to retry slides with errors
            region: Google Cloud region
            skip_visuals: Whether to skip visual generation
            generate_videos: Whether to generate videos
            languages: Comma-separated language locale codes
            style: Optional style/theme for content
        """
        self.folder_path = folder_path
        self.course_id = course_id
        self.retry_errors = retry_errors
        self.region = region
        self.skip_visuals = skip_visuals
        self.generate_videos = generate_videos
        self.languages = languages
        self.style = style
    
    def validate(self) -> None:
        """Validate command parameters."""
        if not os.path.isdir(self.folder_path):
            raise ValueError(f"Folder not found: {self.folder_path}")
    
    def _parse_languages(self) -> List[str]:
        """Parse and normalize language list."""
        lang_list = [lang.strip() for lang in self.languages.split(",")]
        
        # Ensure English is first
        if "en" not in lang_list:
            lang_list.insert(0, "en")
        elif lang_list[0] != "en":
            lang_list.remove("en")
            lang_list.insert(0, "en")
        
        return lang_list
    
    def _find_pptx_files(self) -> List[str]:
        """Find all PPTX/PPTM files in folder."""
        pptx_files = []
        for file in os.listdir(self.folder_path):
            if file.lower().endswith((".pptx", ".pptm")) and not file.startswith('~'):
                pptx_files.append(os.path.join(self.folder_path, file))
        return pptx_files
    
    def _setup_environment(self) -> None:
        """Setup environment variables for batch processing."""
        if self.retry_errors:
            os.environ["SPEAKER_NOTE_RETRY_ERRORS"] = "true"
        else:
            os.environ.pop("SPEAKER_NOTE_RETRY_ERRORS", None)
        
        if self.region:
            os.environ["GOOGLE_CLOUD_LOCATION"] = self.region
    
    async def execute(self) -> None:
        """Execute batch processing."""
        self.validate()
        
        # Find files
        pptx_files = self._find_pptx_files()
        if not pptx_files:
            logger.warning(f"No PPTX/PPTM files found in folder: {self.folder_path}")
            return
        
        # Parse languages
        lang_list = self._parse_languages()
        
        logger.info(f"Found {len(pptx_files)} PPTX/PPTM file(s) to process")
        logger.info(f"Languages to process: {', '.join(lang_list)}")
        
        # Setup environment
        self._setup_environment()
        
        # Process each file
        for idx, pptx_path in enumerate(pptx_files, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing file {idx}/{len(pptx_files)}: "
                       f"{os.path.basename(pptx_path)}")
            logger.info(f"{'='*60}")
            
            # Find corresponding PDF
            pptx_base = os.path.splitext(pptx_path)[0]
            pdf_path = pptx_base + ".pdf"
            
            if not os.path.exists(pdf_path):
                logger.warning(
                    f"PDF not found for {os.path.basename(pptx_path)}, skipping..."
                )
                continue
            
            # Process each language
            for lang in lang_list:
                logger.info(f"\n--- Processing language: {lang} ---")
                
                try:
                    # Create and execute process command
                    cmd = ProcessCommand(
                        pptx_path=pptx_path,
                        pdf_path=pdf_path,
                        course_id=self.course_id,
                        skip_visuals=self.skip_visuals,
                        generate_videos=self.generate_videos,
                        language=lang,
                        style=self.style,
                    )
                    await cmd.execute()
                    
                    logger.info(
                        f"Successfully processed {os.path.basename(pptx_path)} ({lang})"
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing {os.path.basename(pptx_path)} ({lang}): {e}",
                        exc_info=True
                    )
                    # Continue with next language
                    continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Batch processing complete: {len(pptx_files)} file(s) processed")
        logger.info(f"{'='*60}")
