"""Process command for single presentation processing."""

import logging
import os
import sys
from typing import Optional, Tuple

from .base import Command
from config import Config
from services.presentation_processor import PresentationProcessor
from agents.agent_factory import create_all_agents

logger = logging.getLogger(__name__)


class ProcessCommand(Command):
    """Command to process a single presentation."""
    
    def __init__(
        self,
        pptx_path: str,
        pdf_path: str,
        course_id: Optional[str] = None,
        skip_visuals: bool = False,
        generate_videos: bool = False,
        language: str = "en",
        style: Optional[str] = None,
    ):
        """
        Initialize process command.
        
        Args:
            pptx_path: Path to PowerPoint file
            pdf_path: Path to PDF export
            course_id: Optional course ID for context
            skip_visuals: Whether to skip visual generation
            generate_videos: Whether to generate videos
            language: Language locale code
            style: Optional style/theme for content
        """
        self.pptx_path = pptx_path
        self.pdf_path = pdf_path
        self.course_id = course_id
        self.skip_visuals = skip_visuals
        self.generate_videos = generate_videos
        self.language = language
        self.style = style
    
    def validate(self) -> None:
        """Validate command parameters."""
        if not os.path.exists(self.pptx_path):
            raise ValueError(f"PPTX file not found: {self.pptx_path}")
        
        if not os.path.exists(self.pdf_path):
            raise ValueError(f"PDF file not found: {self.pdf_path}")
    
    async def execute(self) -> Tuple[str, Optional[str]]:
        """
        Execute presentation processing.
        
        Returns:
            Tuple of (notes_output_path, visuals_output_path)
        """
        self.validate()
        
        logger.info(f"Processing presentation: {os.path.basename(self.pptx_path)}")
        logger.info(f"Language: {self.language}")
        if self.style:
            logger.info(f"Style: {self.style}")
        
        # Create configuration
        config = Config(
            pptx_path=self.pptx_path,
            pdf_path=self.pdf_path,
            course_id=self.course_id,
            skip_visuals=self.skip_visuals,
            generate_videos=self.generate_videos,
            language=self.language,
            style=self.style,
        )
        
        # Validate configuration
        config.validate()
        
        # Create agents with styles
        agents = create_all_agents(
            visual_style=config.visual_style,
            speaker_style=config.speaker_style
        )
        
        # Create processor
        processor = PresentationProcessor(
            config=config,
            supervisor_agent=agents["supervisor"],
            analyst_agent=agents["analyst"],
            writer_agent=agents["writer"],
            auditor_agent=agents["auditor"],
            overviewer_agent=agents["overviewer"],
            designer_agent=agents["designer"],
            translator_agent=agents["translator"],
            image_translator_agent=agents["image_translator"],
            video_generator_agent=agents["video_generator"],
        )
        
        # Process presentation
        output_path_notes, output_path_visuals = await processor.process()
        
        # Log results
        logger.info("\n" + "="*60)
        logger.info("Processing complete!")
        logger.info(f"1. Notes only: {output_path_notes}")
        if output_path_visuals:
            logger.info(f"2. With visuals: {output_path_visuals}")
        else:
            logger.info("2. With visuals: [SKIPPED - missing images]")
        logger.info("="*60)
        
        return output_path_notes, output_path_visuals
