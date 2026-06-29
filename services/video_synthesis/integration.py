"""Integration utilities for video synthesis with existing services."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from config.config import Config
from services.file_service import FileService
from core.domain.presentation import Presentation
from core.domain.video_synthesis import VideoSynthesisRequest, VideoConfig
from services.video_synthesis.video_synthesis_service import VideoSynthesisService
from services.video_synthesis.integration_helpers import (
    build_video_output_path,
    build_video_synthesis_request,
    load_video_insertions_from_plan,
    resolve_video_synthesis_inputs,
)

logger = logging.getLogger(__name__)


class VideoSynthesisIntegration:
    """Integration layer for video synthesis with existing presentation processing."""
    
    def __init__(self, config: Config):
        """
        Initialize video synthesis integration.
        
        Args:
            config: Main application configuration
        """
        self.config = config
        self.file_service = FileService()
        
        # Initialize video synthesis service if enabled
        self.video_service = None
        if config.enable_video_synthesis:
            temp_dir = Path(config.video_synthesis_dir) / "temp"
            self.video_service = VideoSynthesisService(temp_dir=temp_dir)
    
    def is_video_synthesis_enabled(self) -> bool:
        """Check if video synthesis is enabled and available."""
        return self.config.enable_video_synthesis and self.video_service is not None
    
    def create_video_from_presentation(
        self,
        presentation: Presentation,
        slide_images_dir: Optional[Path] = None,
        audio_files_dir: Optional[Path] = None,
        output_filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Create video from presentation slides and audio files.
        
        Args:
            presentation: Presentation domain object
            slide_images_dir: Directory containing slide images
            audio_files_dir: Directory containing audio files
            output_filename: Optional custom output filename
            
        Returns:
            Path to generated video file or None if synthesis failed
        """
        if not self.is_video_synthesis_enabled():
            logger.warning("Video synthesis is not enabled")
            return None
        
        try:
            logger.info(f"Creating video from presentation: {presentation.pptx_path.name}")
            
            # Use appropriate directories if not specified
            slide_images_dir, audio_files_dir = resolve_video_synthesis_inputs(
                self.config, slide_images_dir, audio_files_dir
            )
            
            # Find slide images and audio files
            slide_images = self._find_slide_images(slide_images_dir, presentation.total_slides())
            audio_files = self._find_audio_files(audio_files_dir, presentation.total_slides())
            
            if not slide_images or not audio_files:
                logger.warning("No slide images or audio files found for video synthesis")
                return None
            
            if len(slide_images) != len(audio_files):
                logger.warning(f"Mismatch: {len(slide_images)} images, {len(audio_files)} audio files")
                return None
            
            # Generate output path
            output_path = build_video_output_path(self.config, presentation, output_filename)
            inserted_video_paths_before = load_video_insertions_from_plan(Path(self.config.videos_dir))
            
            # Get video configuration
            video_config = self.config.get_video_synthesis_config()
            if not video_config:
                logger.error("Failed to get video synthesis configuration")
                return None
            
            # Create synthesis request
            request = build_video_synthesis_request(
                presentation=presentation,
                slide_images=slide_images,
                audio_files=audio_files,
                output_path=output_path,
                config=video_config,
                inserted_video_paths_before=inserted_video_paths_before,
            )
            
            # Synthesize video
            result = self.video_service.synthesize_video(request)
            
            if result.success:
                logger.info(f"Video synthesis completed: {result.output_path}")
                return result.output_path
            else:
                logger.error(f"Video synthesis failed: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating video from presentation: {e}")
            return None
    
    def create_video_from_presentation_directories(
        self,
        presentation: Presentation,
        output_filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Create video from presentation using the standard visuals and speech directories.
        
        This is a convenience method that uses the visuals directory for slide images
        and the speech directory for MP3 audio files.
        
        Args:
            presentation: Presentation domain object
            output_filename: Optional custom output filename
            
        Returns:
            Path to generated video file or None if synthesis failed
        """
        visuals_dir = Path(self.config.visuals_dir)
        speech_dir = Path(self.config.speech_dir)
        return self.create_video_from_presentation(
            presentation=presentation,
            slide_images_dir=visuals_dir,
            audio_files_dir=speech_dir,
            output_filename=output_filename
        )
    
    def create_video_from_slide_audio_pairs(
        self,
        slide_audio_pairs: List[tuple[Path, Path]],
        output_path: Path,
        presentation_id: str = "custom",
        video_config: Optional[VideoConfig] = None
    ) -> Optional[Path]:
        """
        Create video from explicit slide-audio pairs.
        
        Args:
            slide_audio_pairs: List of (slide_image_path, audio_file_path) tuples
            output_path: Output video file path
            presentation_id: Identifier for the presentation
            video_config: Optional video configuration
            
        Returns:
            Path to generated video file or None if synthesis failed
        """
        if not self.is_video_synthesis_enabled():
            logger.warning("Video synthesis is not enabled")
            return None
        
        try:
            logger.info(f"Creating video from {len(slide_audio_pairs)} slide-audio pairs")
            
            # Extract slide images and audio files
            slide_images = [pair[0] for pair in slide_audio_pairs]
            audio_files = [pair[1] for pair in slide_audio_pairs]
            
            # Use provided config or get default
            config = video_config or self.config.get_video_synthesis_config()
            if not config:
                logger.error("Failed to get video synthesis configuration")
                return None
            
            # Create synthesis request
            request = VideoSynthesisRequest(
                slide_images=slide_images,
                audio_files=audio_files,
                output_path=output_path,
                config=config,
                presentation_id=presentation_id
            )
            
            # Synthesize video
            result = self.video_service.synthesize_video(request)
            
            if result.success:
                logger.info(f"Video synthesis completed: {result.output_path}")
                return result.output_path
            else:
                logger.error(f"Video synthesis failed: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating video from slide-audio pairs: {e}")
            return None
    
    def _find_slide_images(self, images_dir: Path, expected_count: int) -> List[Path]:
        """
        Find slide images in directory.
        
        Args:
            images_dir: Directory to search for images
            expected_count: Expected number of images
            
        Returns:
            List of image file paths in order
        """
        if not images_dir.exists():
            logger.warning(f"Images directory not found: {images_dir}")
            return []
        
        # Look for common slide image patterns
        image_patterns = [
            "slide_*.png", "slide_*.jpg", "slide_*.jpeg",
            "Slide_*.png", "Slide_*.jpg", "Slide_*.jpeg",
            "*_slide_*.png", "*_slide_*.jpg", "*_slide_*.jpeg"
        ]
        
        found_images = []
        for pattern in image_patterns:
            images = list(images_dir.glob(pattern))
            if images:
                found_images.extend(images)
                break
        
        if not found_images:
            # Fallback: look for any image files
            for ext in ['.png', '.jpg', '.jpeg']:
                images = list(images_dir.glob(f"*{ext}"))
                if images:
                    found_images.extend(images)
                    break
        
        # Sort by filename to ensure correct order
        found_images.sort(key=lambda x: x.name)
        
        logger.debug(f"Found {len(found_images)} slide images (expected {expected_count})")
        return found_images[:expected_count]  # Limit to expected count
    
    def _find_audio_files(self, audio_dir: Path, expected_count: int) -> List[Path]:
        """
        Find audio files in directory.
        
        Args:
            audio_dir: Directory to search for audio files
            expected_count: Expected number of audio files
            
        Returns:
            List of audio file paths in order
        """
        if not audio_dir.exists():
            logger.warning(f"Audio directory not found: {audio_dir}")
            return []
        
        # Look for common audio file patterns
        audio_patterns = [
            "slide_*.mp3", "audio_*.mp3", "speech_*.mp3",
            "Slide_*.mp3", "Audio_*.mp3", "Speech_*.mp3"
        ]
        
        found_audio = []
        for pattern in audio_patterns:
            audio_files = list(audio_dir.glob(pattern))
            if audio_files:
                found_audio.extend(audio_files)
                break
        
        if not found_audio:
            # Fallback: look for any MP3 files
            audio_files = list(audio_dir.glob("*.mp3"))
            if audio_files:
                found_audio.extend(audio_files)
        
        # Sort by filename to ensure correct order
        found_audio.sort(key=lambda x: x.name)
        
        logger.debug(f"Found {len(found_audio)} audio files (expected {expected_count})")
        return found_audio[:expected_count]  # Limit to expected count
    
    def get_video_synthesis_status(self) -> Dict[str, Any]:
        """
        Get status of video synthesis capability.
        
        Returns:
            Dictionary with status information
        """
        status = {
            'enabled': self.config.enable_video_synthesis,
            'service_available': self.video_service is not None,
            'output_directory': self.config.video_synthesis_dir if self.config.enable_video_synthesis else None
        }
        
        if self.video_service:
            status['supported_formats'] = self.video_service.get_supported_formats()
        
        return status


def create_video_synthesis_integration(config: Config) -> VideoSynthesisIntegration:
    """
    Factory function to create video synthesis integration.
    
    Args:
        config: Main application configuration
        
    Returns:
        VideoSynthesisIntegration instance
    """
    return VideoSynthesisIntegration(config)