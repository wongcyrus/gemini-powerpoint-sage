"""Video generation service."""

import logging
import os
from typing import Optional

import pymupdf
from PIL import Image
from google.adk.agents import LlmAgent

from config.constants import FilePatterns
from utils.agent_utils import run_stateless_agent
from utils.error_handling import VideoGenerationError
from services.video_service_helpers import (
    build_video_agent_prompt,
    build_video_prompt,
    extract_artifact_id,
    format_video_prompt_file,
)

logger = logging.getLogger(__name__)


class VideoService:
    """Service for generating video prompts and videos."""
    
    def __init__(
        self,
        video_generator_agent: Optional[LlmAgent] = None,
        videos_dir: Optional[str] = None,
    ):
        """
        Initialize video service.
        
        Args:
            video_generator_agent: Agent for generating videos
            videos_dir: Directory to save video outputs
        """
        self.video_generator_agent = video_generator_agent
        self.videos_dir = videos_dir
        
        if videos_dir:
            os.makedirs(videos_dir, exist_ok=True)
    
    async def generate_video_prompt(
        self,
        slide_idx: int,
        speaker_notes: str,
        slide_image: Optional[Image.Image] = None,
    ) -> str:
        """
        Generate a video prompt for a slide.
        
        Args:
            slide_idx: Slide index
            speaker_notes: Speaker notes for the slide
            slide_image: Optional slide image for context
            
        Returns:
            Video prompt text
        """
        return build_video_prompt(speaker_notes)
    
    async def generate_video(
        self,
        slide_idx: int,
        speaker_notes: str,
        slide_image: Optional[Image.Image] = None,
    ) -> Optional[str]:
        """
        Generate a video for a slide using the video agent.
        
        Args:
            slide_idx: Slide index
            speaker_notes: Speaker notes
            slide_image: Optional slide image
            
        Returns:
            Video artifact ID or None if generation failed
        """
        if not self.video_generator_agent:
            logger.warning("Video generator agent not available")
            return None
        
        try:
            # Generate video prompt
            video_prompt = await self.generate_video_prompt(
                slide_idx, speaker_notes, slide_image
            )
            
            # Call video agent
            agent_prompt = build_video_agent_prompt(video_prompt, speaker_notes)
            
            images = [slide_image] if slide_image else None
            response = await run_stateless_agent(
                self.video_generator_agent,
                agent_prompt,
                images=images
            )
            
            # Extract artifact ID from response
            artifact_id = self._extract_artifact_id(response)
            
            if artifact_id:
                logger.info(
                    f"Generated video artifact for Slide {slide_idx}: "
                    f"{artifact_id}"
                )
                return artifact_id
            else:
                logger.warning(
                    f"No video artifact in response for Slide {slide_idx}"
                )
                return None
                
        except Exception as e:
            logger.error(
                f"Video generation failed for Slide {slide_idx}: {e}",
                exc_info=True
            )
            return None
    
    async def save_video_prompt(
        self,
        slide_idx: int,
        video_prompt: str,
        speaker_notes: str,
        video_artifact: Optional[str] = None,
    ) -> str:
        """
        Save video prompt to file.
        
        Args:
            slide_idx: Slide index
            video_prompt: Video prompt text
            speaker_notes: Speaker notes
            video_artifact: Optional video artifact ID
            
        Returns:
            Path to saved prompt file
        """
        if not self.videos_dir:
            raise VideoGenerationError("Videos directory not configured")
        
        filename = FilePatterns.VIDEO_PROMPT_FILE.format(idx=slide_idx)
        filepath = os.path.join(self.videos_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(
                format_video_prompt_file(
                    slide_idx,
                    video_prompt,
                    speaker_notes,
                    video_artifact,
                )
            )
        
        logger.info(f"Saved video prompt to {filepath}")
        return filepath
    
    def _extract_artifact_id(self, agent_response: str) -> str:
        """
        Extract artifact ID from agent response.
        
        Args:
            agent_response: Full text response from agent
            
        Returns:
            Artifact ID if found, empty string otherwise
        """
        return extract_artifact_id(agent_response)
    
    def is_available(self) -> bool:
        """Check if video generation is available."""
        return self.video_generator_agent is not None
