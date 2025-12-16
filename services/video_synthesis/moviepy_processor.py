"""MoviePy video processing engine for video synthesis."""

import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING

try:
    from moviepy import (
        VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip,
        concatenate_videoclips, ColorClip
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        # Fallback to older import style
        from moviepy.editor import (
            VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip,
            concatenate_videoclips, ColorClip
        )
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False

from core.domain.video_synthesis import (
    VideoConfig, SlideVideoSegment, VideoProcessingError
)

if TYPE_CHECKING:
    from .file_manager import VideoFileManager

logger = logging.getLogger(__name__)


class MoviePyVideoProcessor:
    """Core video processing engine using MoviePy."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        """
        Initialize MoviePy video processor.
        
        Args:
            temp_dir: Optional temporary directory for intermediate files
        """
        if not MOVIEPY_AVAILABLE:
            raise VideoProcessingError(
                "MoviePy is required for video processing. Install it with: pip install moviepy"
            )
        
        self.temp_dir = temp_dir or Path(tempfile.gettempdir())
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("MoviePy video processor initialized")
    
    def create_video_segment(
        self,
        segment: SlideVideoSegment,
        config: VideoConfig,
        temp_dir: Path,
        file_manager: Optional['VideoFileManager'] = None
    ) -> Path:
        """
        Convert a slide image and audio into a video segment using MoviePy.
        
        Args:
            segment: Slide video segment with image, audio, and duration
            config: Video configuration settings
            temp_dir: Temporary directory for intermediate files
            file_manager: Optional file manager for caching support
            
        Returns:
            Path to generated video segment file
            
        Raises:
            VideoProcessingError: If video segment creation fails
        """
        try:
            logger.debug(f"Creating video segment for slide {segment.slide_index} using MoviePy")
            
            # Check cache first if file manager is provided
            if file_manager and file_manager.enable_cache:
                config_dict = {
                    'resolution': config.resolution,
                    'fps': config.fps,
                    'video_codec': config.video_codec,
                    'audio_codec': config.audio_codec,
                    'video_bitrate': config.video_bitrate,
                    'audio_bitrate': config.audio_bitrate,
                    'output_format': config.output_format,
                    'fade_duration': config.fade_duration
                }
                
                cache_key = file_manager.generate_segment_cache_key(
                    segment.image_path, segment.audio_path, config_dict
                )
                
                cached_segment = file_manager.get_cached_segment(cache_key, config.output_format)
                if cached_segment:
                    # Copy cached segment to temp directory
                    import shutil
                    segment_filename = f"segment_{segment.slide_index:03d}.{config.output_format}"
                    segment_output_path = temp_dir / segment_filename
                    shutil.copy2(cached_segment, segment_output_path)
                    
                    # Update segment with temp video path
                    segment.temp_video_path = segment_output_path
                    
                    logger.info(f"Using cached segment for slide {segment.slide_index}")
                    return segment_output_path
            
            # Generate output filename
            segment_filename = f"segment_{segment.slide_index:03d}.{config.output_format}"
            segment_output_path = temp_dir / segment_filename
            
            # Load audio clip
            logger.debug(f"Loading audio: {segment.audio_path}")
            audio_clip = AudioFileClip(str(segment.audio_path))
            
            # Load image and create video clip
            logger.debug(f"Loading image: {segment.image_path}")
            image_clip = ImageClip(str(segment.image_path))
            
            # Set duration to match audio
            image_clip = image_clip.with_duration(audio_clip.duration)
            
            # Resize image to match target resolution while maintaining aspect ratio
            target_width, target_height = config.resolution
            
            # For large presentations, use more conservative resizing to avoid memory issues
            img_width, img_height = image_clip.size
            
            # If the image is very large, resize it down first to avoid memory issues
            if img_width > 2048 or img_height > 2048:
                # Pre-resize very large images to a reasonable size
                max_dimension = 1920
                if img_width > img_height:
                    pre_width = max_dimension
                    pre_height = int(img_height * max_dimension / img_width)
                else:
                    pre_height = max_dimension
                    pre_width = int(img_width * max_dimension / img_height)
                
                image_clip = image_clip.resized((pre_width, pre_height))
                img_width, img_height = pre_width, pre_height
            
            # Calculate scaling to fit within target resolution
            scale_width = target_width / img_width
            scale_height = target_height / img_height
            scale = min(scale_width, scale_height)
            
            # Resize image
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            image_clip = image_clip.resized((new_width, new_height))
            
            # Center the image on a black background of target resolution
            if new_width != target_width or new_height != target_height:
                # Create black background (ColorClip already imported)
                background = ColorClip(
                    size=config.resolution,
                    color=(0, 0, 0),
                    duration=audio_clip.duration
                )
                
                # Center the image
                x_offset = (target_width - new_width) // 2
                y_offset = (target_height - new_height) // 2
                
                image_clip = image_clip.with_position((x_offset, y_offset))
                video_clip = CompositeVideoClip([background, image_clip])
            else:
                video_clip = image_clip
            
            # Set FPS
            video_clip = video_clip.with_fps(config.fps)
            
            # Add audio
            final_clip = video_clip.with_audio(audio_clip)
            
            # Apply fade effects if configured
            if config.fade_duration > 0:
                fade_duration = min(config.fade_duration, audio_clip.duration / 4)  # Max 25% of clip duration
                try:
                    # Use the correct MoviePy 2.x API for fade effects
                    from moviepy.video.fx.FadeIn import FadeIn
                    from moviepy.video.fx.FadeOut import FadeOut
                    final_clip = final_clip.with_effects([FadeIn(fade_duration), FadeOut(fade_duration)])
                except ImportError:
                    logger.warning("Fade effects not available in this MoviePy version")
            
            logger.debug(f"Writing video segment: {segment_output_path}")
            
            # Write video file
            codec_params = self._get_codec_params(config)
            
            final_clip.write_videofile(
                str(segment_output_path),
                fps=config.fps,
                **codec_params
            )
            
            # Clean up clips to free memory
            final_clip.close()
            video_clip.close()
            image_clip.close()
            audio_clip.close()
            if 'background' in locals():
                background.close()
            
            # Verify output file was created
            if not segment_output_path.exists():
                raise VideoProcessingError(f"Failed to create video segment: {segment_output_path}")
            
            # Cache the segment if file manager is provided
            if file_manager and file_manager.enable_cache:
                try:
                    file_manager.cache_segment(segment_output_path, cache_key)
                except Exception as e:
                    logger.warning(f"Failed to cache segment for slide {segment.slide_index}: {e}")
            
            # Update segment with temp video path
            segment.temp_video_path = segment_output_path
            
            logger.debug(f"Successfully created video segment: {segment_output_path}")
            return segment_output_path
            
        except Exception as e:
            # Clean up any clips that might be open
            try:
                if 'final_clip' in locals():
                    final_clip.close()
                if 'video_clip' in locals():
                    video_clip.close()
                if 'image_clip' in locals():
                    image_clip.close()
                if 'audio_clip' in locals():
                    audio_clip.close()
                if 'background' in locals():
                    background.close()
            except:
                pass  # Ignore cleanup errors
            
            error_msg = f"Failed to create video segment for slide {segment.slide_index}: {e}"
            logger.error(error_msg)
            raise VideoProcessingError(error_msg) from e
    
    def _get_codec_params(self, config: VideoConfig) -> Dict[str, Any]:
        """
        Get codec-specific parameters for MoviePy.
        
        Args:
            config: Video configuration
            
        Returns:
            Dictionary of codec parameters
        """
        # Use optimized parameters for faster processing
        params = {
            'remove_temp': True,
            'preset': 'ultrafast',  # Fastest encoding preset
            'threads': 4,           # Use multiple threads
        }
        
        return params
    
    def concatenate_segments(
        self,
        segments: List[SlideVideoSegment],
        config: VideoConfig,
        output_path: Path,
        temp_dir: Path
    ) -> Path:
        """
        Concatenate multiple video segments into final video using MoviePy.
        
        Args:
            segments: List of video segments to concatenate
            config: Video configuration
            output_path: Final output video path
            temp_dir: Temporary directory for intermediate files
            
        Returns:
            Path to final concatenated video
            
        Raises:
            VideoProcessingError: If concatenation fails
        """
        clips = []
        
        try:
            logger.info(f"Concatenating {len(segments)} video segments using MoviePy")
            
            if not segments:
                raise VideoProcessingError("No video segments to concatenate")
            
            # Verify all segments have temp video paths
            for i, segment in enumerate(segments):
                if not segment.temp_video_path or not segment.temp_video_path.exists():
                    raise VideoProcessingError(f"Missing video segment file for slide {i}")
            
            # Load all video clips
            for i, segment in enumerate(segments):
                logger.debug(f"Loading segment {i+1}/{len(segments)}: {segment.temp_video_path}")
                try:
                    clip = VideoFileClip(str(segment.temp_video_path))
                    clips.append(clip)
                except Exception as e:
                    # Clean up already loaded clips
                    for loaded_clip in clips:
                        loaded_clip.close()
                    raise VideoProcessingError(f"Failed to load video segment {i}: {e}")
            
            # Handle single segment case
            if len(clips) == 1:
                logger.debug("Single segment - copying to output")
                final_clip = clips[0]
            else:
                # Concatenate multiple segments
                logger.debug(f"Concatenating {len(clips)} video clips")
                
                if config.fade_duration > 0:
                    # Apply crossfade transitions
                    final_clip = self._concatenate_with_crossfade(clips, config.fade_duration)
                else:
                    # Simple concatenation
                    final_clip = concatenate_videoclips(clips, method="compose")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write final video
            logger.info(f"Writing final video to: {output_path}")
            codec_params = self._get_codec_params(config)
            
            final_clip.write_videofile(
                str(output_path),
                fps=config.fps,
                **codec_params
            )
            
            # Clean up clips
            final_clip.close()
            for clip in clips:
                clip.close()
            
            # Verify output file was created
            if not output_path.exists():
                raise VideoProcessingError(f"Failed to create final video: {output_path}")
            
            logger.info(f"Successfully created final video: {output_path}")
            return output_path
            
        except Exception as e:
            # Clean up clips in case of error
            try:
                if 'final_clip' in locals():
                    final_clip.close()
                for clip in clips:
                    clip.close()
            except:
                pass  # Ignore cleanup errors
            
            error_msg = f"Failed to concatenate video segments: {e}"
            logger.error(error_msg)
            raise VideoProcessingError(error_msg) from e
    
    def _concatenate_with_crossfade(self, clips: List, fade_duration: float):
        """
        Concatenate clips with crossfade transitions.
        
        Args:
            clips: List of video clips
            fade_duration: Duration of crossfade in seconds
            
        Returns:
            Final concatenated clip with crossfades
        """
        if len(clips) <= 1:
            return clips[0] if clips else None
        
        logger.debug(f"Applying crossfade transitions with {fade_duration}s duration")
        
        # Apply fade effects to each clip
        processed_clips = []
        
        for i, clip in enumerate(clips):
            # Calculate actual fade duration (don't exceed 25% of clip duration)
            actual_fade = min(fade_duration, clip.duration / 4)
            
            try:
                # Use the correct MoviePy 2.x API for fade effects
                from moviepy.video.fx.FadeIn import FadeIn
                from moviepy.video.fx.FadeOut import FadeOut
                
                if i == 0:
                    # First clip: only fade out at the end
                    processed_clip = clip.with_effects([FadeOut(actual_fade)])
                elif i == len(clips) - 1:
                    # Last clip: only fade in at the beginning
                    processed_clip = clip.with_effects([FadeIn(actual_fade)])
                else:
                    # Middle clips: fade in and out
                    processed_clip = clip.with_effects([FadeIn(actual_fade), FadeOut(actual_fade)])
            except ImportError:
                logger.warning("Fade effects not available, using clips without fades")
                processed_clip = clip
            
            processed_clips.append(processed_clip)
        
        # Concatenate with overlap for smooth transitions
        try:
            # Use negative padding to create overlap
            overlap_duration = min(fade_duration, 0.5)  # Max 0.5s overlap
            final_clip = concatenate_videoclips(
                processed_clips, 
                padding=-overlap_duration, 
                method="compose"
            )
            return final_clip
        except Exception as e:
            logger.warning(f"Crossfade concatenation failed: {e}, falling back to simple concatenation")
            # Fallback to simple concatenation
            return concatenate_videoclips(processed_clips, method="compose")
    
    def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """
        Get information about a video file using MoviePy.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary containing video information
            
        Raises:
            VideoProcessingError: If video info extraction fails
        """
        try:
            logger.debug(f"Getting video info for: {video_path}")
            
            # Load video clip to get info
            clip = VideoFileClip(str(video_path))
            
            info = {
                'duration_seconds': clip.duration,
                'width': clip.w,
                'height': clip.h,
                'fps': clip.fps,
                'file_size_bytes': video_path.stat().st_size if video_path.exists() else 0
            }
            
            # Add audio info if available
            if clip.audio:
                info.update({
                    'has_audio': True,
                    'audio_fps': clip.audio.fps if hasattr(clip.audio, 'fps') else None
                })
            else:
                info['has_audio'] = False
            
            # Clean up
            clip.close()
            
            return info
            
        except Exception as e:
            error_msg = f"Failed to get video info for {video_path}: {e}"
            logger.error(error_msg)
            raise VideoProcessingError(error_msg) from e