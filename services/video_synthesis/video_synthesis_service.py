"""Main video synthesis service orchestrator."""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from core.domain.video_synthesis import (
    VideoSynthesisRequest, VideoSynthesisResult, VideoConfig,
    SlideVideoSegment, VideoSynthesisError, VideoProcessingError,
    AudioAnalysisError, FileValidationError
)
from services.video_synthesis.audio_analyzer import AudioAnalyzer
from services.video_synthesis.file_validator import FileValidator
from services.video_synthesis.video_config_manager import VideoConfigManager
from services.video_synthesis.ffmpeg_processor import FFmpegVideoProcessor
from services.video_synthesis.file_manager import VideoFileManager
from services.video_synthesis.progress_tracker import (
    VideoProgressTracker, ProcessingStage, ProgressReporter
)

logger = logging.getLogger(__name__)


class VideoSynthesisService:
    """Main orchestrator service for video synthesis operations."""
    
    def __init__(
        self,
        temp_dir: Optional[Path] = None,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize video synthesis service.
        
        Args:
            temp_dir: Optional temporary directory for processing
            progress_callback: Optional callback for progress updates
        """
        self.temp_dir = temp_dir
        self.progress_callback = progress_callback
        
        # Initialize components
        self.audio_analyzer = AudioAnalyzer()
        self.file_validator = FileValidator()
        self.config_manager = VideoConfigManager()
        
        logger.info("VideoSynthesisService initialized")
    
    def synthesize_video(
        self,
        request: VideoSynthesisRequest,
        progress_callback: Optional[Callable] = None
    ) -> VideoSynthesisResult:
        """
        Main method to synthesize video from slides and audio.
        
        Args:
            request: Video synthesis request
            progress_callback: Optional progress callback
            
        Returns:
            VideoSynthesisResult with operation outcome
        """
        start_time = time.time()
        operation_id = f"video_synthesis_{int(start_time)}"
        
        # Use provided callback or instance callback
        callback = progress_callback or self.progress_callback
        
        # Initialize progress tracker
        progress_tracker = VideoProgressTracker(operation_id, len(request.slide_images))
        if callback:
            progress_tracker.add_progress_callback(callback)
        
        # Initialize file manager
        file_manager = VideoFileManager(self.temp_dir, operation_id)
        
        try:
            logger.info(f"Starting video synthesis: {operation_id}")
            
            # Stage 1: Validation
            progress_tracker.update_stage(ProcessingStage.VALIDATING, "Validating input files and configuration")
            self._validate_request(request, progress_tracker)
            
            # Stage 2: Audio Analysis
            progress_tracker.update_stage(ProcessingStage.ANALYZING_AUDIO, "Analyzing audio files")
            segments = self._analyze_audio_files(request, progress_tracker)
            
            # Stage 3: Create video segments
            progress_tracker.update_stage(ProcessingStage.CREATING_SEGMENTS, "Creating video segments")
            temp_segments = self._create_video_segments(segments, request.config, file_manager, progress_tracker)
            
            # Stage 4: Concatenate segments
            progress_tracker.update_stage(ProcessingStage.CONCATENATING, "Concatenating video segments")
            temp_output = self._concatenate_segments(temp_segments, request.config, file_manager, progress_tracker)
            
            # Stage 5: Finalize output
            progress_tracker.update_stage(ProcessingStage.FINALIZING, "Finalizing output video")
            final_output = self._finalize_output(temp_output, request.output_path, file_manager, progress_tracker)
            
            # Calculate final statistics
            processing_time = time.time() - start_time
            file_size = final_output.stat().st_size
            
            # Get video duration - use estimated duration to avoid hanging
            try:
                # Try to get video info with a short timeout
                ffmpeg_processor = FFmpegVideoProcessor()
                video_info = ffmpeg_processor.get_video_info(final_output)
                video_duration = video_info.get('duration_seconds', 0)
            except Exception as e:
                logger.warning(f"Failed to get video info (this is common and not critical): {e}")
                # Fallback: estimate duration from segments
                video_duration = sum(segment.duration_seconds for segment in segments)
                video_info = {
                    'duration_seconds': video_duration,
                    'estimated': True,
                    'error': str(e)
                }
            
            # Mark as completed - with timeout protection
            try:
                progress_tracker.mark_completed(final_output, file_size, video_duration)
            except Exception as e:
                logger.warning(f"Progress tracker completion failed (non-critical): {e}")
                # Continue anyway - the video was created successfully
            
            # Create success result
            result = VideoSynthesisResult.success_result(
                output_path=final_output,
                duration_seconds=video_duration,
                file_size_bytes=file_size,
                processing_time_seconds=processing_time,
                slides_processed=len(request.slide_images),
                metadata={
                    'operation_id': operation_id,
                    'video_info': video_info,
                    'config_summary': self.config_manager.get_config_summary(request.config)
                }
            )
            
            logger.info(f"Video synthesis completed successfully: {final_output}")
            return result
            
        except Exception as e:
            # Mark as failed and handle cleanup
            progress_tracker.mark_failed(e)
            
            # Clean up temporary files
            cleanup_status = file_manager.cleanup(force=True)
            
            processing_time = time.time() - start_time
            
            # Create failure result
            result = VideoSynthesisResult.failure_result(
                error_message=str(e),
                processing_time_seconds=processing_time,
                slides_processed=progress_tracker.current_slide,
                metadata={
                    'operation_id': operation_id,
                    'error_type': type(e).__name__,
                    'cleanup_status': cleanup_status
                }
            )
            
            logger.error(f"Video synthesis failed: {e}")
            return result
        
        finally:
            # Ensure cleanup happens
            try:
                file_manager.cleanup()
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")
    
    def _validate_request(self, request: VideoSynthesisRequest, progress_tracker: VideoProgressTracker) -> None:
        """
        Validate synthesis request.
        
        Args:
            request: Video synthesis request
            progress_tracker: Progress tracker
            
        Raises:
            FileValidationError: If validation fails
        """
        try:
            logger.debug("Validating synthesis request")
            
            # Validate basic request structure
            request.validate()
            
            # Validate slide-audio pairs
            self.file_validator.validate_slide_audio_pairs(request.slide_images, request.audio_files)
            
            # Validate output path
            self.file_validator.validate_output_path(request.output_path)
            
            # Validate configuration
            self.config_manager.validate_config(request.config)
            
            logger.debug("Request validation completed successfully")
            
        except Exception as e:
            progress_tracker.report_error(e)
            raise FileValidationError(f"Request validation failed: {e}") from e
    
    def _analyze_audio_files(self, request: VideoSynthesisRequest, progress_tracker: VideoProgressTracker) -> list[SlideVideoSegment]:
        """
        Analyze audio files and create segments.
        
        Args:
            request: Video synthesis request
            progress_tracker: Progress tracker
            
        Returns:
            List of slide video segments
            
        Raises:
            AudioAnalysisError: If audio analysis fails
        """
        try:
            logger.debug("Analyzing audio files")
            
            segments = []
            
            for i, (image_path, audio_path) in enumerate(zip(request.slide_images, request.audio_files)):
                progress_tracker.update_slide_progress(
                    i, ProcessingStage.ANALYZING_AUDIO,
                    f"Analyzing audio for slide {i+1}: {audio_path.name}"
                )
                
                try:
                    # Create segment with duration extraction
                    segment = SlideVideoSegment.from_files(i, image_path, audio_path)
                    segments.append(segment)
                    
                    logger.debug(f"Analyzed slide {i+1}: {segment.duration_seconds:.3f}s")
                    
                except Exception as e:
                    progress_tracker.report_error(e, i)
                    raise AudioAnalysisError(f"Failed to analyze audio for slide {i+1}: {e}") from e
            
            total_duration = sum(segment.duration_seconds for segment in segments)
            logger.info(f"Audio analysis completed: {len(segments)} segments, total duration {total_duration:.2f}s")
            
            return segments
            
        except Exception as e:
            if not isinstance(e, AudioAnalysisError):
                progress_tracker.report_error(e)
                raise AudioAnalysisError(f"Audio analysis failed: {e}") from e
            raise
    
    def _create_video_segments(
        self,
        segments: list[SlideVideoSegment],
        config: VideoConfig,
        file_manager: VideoFileManager,
        progress_tracker: VideoProgressTracker
    ) -> list[SlideVideoSegment]:
        """
        Create video segments from slide-audio pairs.
        
        Args:
            segments: List of slide video segments
            config: Video configuration
            file_manager: File manager
            progress_tracker: Progress tracker
            
        Returns:
            List of segments with temp video paths
            
        Raises:
            VideoProcessingError: If segment creation fails
        """
        try:
            logger.info(f"Creating {len(segments)} video segments")
            
            # Create segments directory
            segments_dir = file_manager.create_segment_temp_dir()
            
            # Initialize FFmpeg processor
            ffmpeg_processor = FFmpegVideoProcessor(segments_dir)
            
            processed_segments = []
            
            for i, segment in enumerate(segments):
                progress_tracker.update_slide_progress(
                    i, ProcessingStage.CREATING_SEGMENTS,
                    f"Creating video segment {i+1}/{len(segments)}: {segment.image_path.name}"
                )
                
                try:
                    # Create video segment with caching support
                    segment_path = ffmpeg_processor.create_video_segment(segment, config, segments_dir, file_manager)
                    
                    # Update segment with temp path
                    segment.temp_video_path = segment_path
                    processed_segments.append(segment)
                    
                    logger.debug(f"Created video segment {i+1}: {segment_path}")
                    
                except Exception as e:
                    progress_tracker.report_error(e, i)
                    raise VideoProcessingError(f"Failed to create video segment {i+1}: {e}") from e
            
            logger.info(f"Successfully created {len(processed_segments)} video segments")
            return processed_segments
            
        except Exception as e:
            if not isinstance(e, VideoProcessingError):
                progress_tracker.report_error(e)
                raise VideoProcessingError(f"Video segment creation failed: {e}") from e
            raise
    
    def _concatenate_segments(
        self,
        segments: list[SlideVideoSegment],
        config: VideoConfig,
        file_manager: VideoFileManager,
        progress_tracker: VideoProgressTracker
    ) -> Path:
        """
        Concatenate video segments into final video.
        
        Args:
            segments: List of video segments
            config: Video configuration
            file_manager: File manager
            progress_tracker: Progress tracker
            
        Returns:
            Path to concatenated video file
            
        Raises:
            VideoProcessingError: If concatenation fails
        """
        try:
            logger.info("Concatenating video segments")
            
            progress_tracker.update_stage(
                ProcessingStage.CONCATENATING,
                f"Concatenating {len(segments)} video segments"
            )
            
            # Create working directory for concatenation
            concat_dir = file_manager.create_working_temp_dir("concatenation")
            
            # Generate temporary output filename
            temp_output_path = file_manager.get_temp_file_path(
                f"concatenated_video.{config.output_format}",
                "concatenation"
            )
            
            # Initialize FFmpeg processor
            ffmpeg_processor = FFmpegVideoProcessor(concat_dir)
            
            # Concatenate segments
            final_path = ffmpeg_processor.concatenate_segments(segments, config, temp_output_path, concat_dir)
            
            logger.info(f"Successfully concatenated video: {final_path}")
            return final_path
            
        except Exception as e:
            progress_tracker.report_error(e)
            raise VideoProcessingError(f"Video concatenation failed: {e}") from e
    
    def _finalize_output(
        self,
        temp_output: Path,
        final_output_path: Path,
        file_manager: VideoFileManager,
        progress_tracker: VideoProgressTracker
    ) -> Path:
        """
        Finalize output by moving to final location.
        
        Args:
            temp_output: Temporary output file path
            final_output_path: Final output file path
            file_manager: File manager
            progress_tracker: Progress tracker
            
        Returns:
            Path to final output file
            
        Raises:
            VideoSynthesisError: If finalization fails
        """
        try:
            logger.info(f"Finalizing output: {final_output_path}")
            
            progress_tracker.update_stage(
                ProcessingStage.FINALIZING,
                f"Moving video to final location: {final_output_path.name}"
            )
            
            # Move to final location
            final_path = file_manager.move_to_output(temp_output, final_output_path)
            
            logger.info(f"Video finalized: {final_path}")
            return final_path
            
        except Exception as e:
            progress_tracker.report_error(e)
            raise VideoSynthesisError(f"Output finalization failed: {e}") from e
    
    def cancel_operation(self, operation_id: str) -> Dict[str, Any]:
        """
        Cancel an ongoing video synthesis operation.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Cancellation status
        """
        # This would be implemented with a registry of active operations
        # For now, return a placeholder
        logger.warning(f"Cancellation requested for operation {operation_id} (not implemented)")
        return {'cancelled': False, 'reason': 'Cancellation not implemented'}
    
    def get_supported_formats(self) -> Dict[str, list[str]]:
        """
        Get supported file formats.
        
        Returns:
            Dictionary with supported formats
        """
        return {
            'image_formats': list(self.file_validator.supported_image_formats),
            'audio_formats': list(self.file_validator.supported_audio_formats),
            'video_formats': ['mp4', 'avi', 'mkv', 'webm']
        }
    
    def create_default_config(self) -> VideoConfig:
        """
        Create default video configuration.
        
        Returns:
            Default VideoConfig instance
        """
        return self.config_manager.create_default_config()
    
    def create_optimized_config(self, total_duration: float, slide_count: int) -> VideoConfig:
        """
        Create optimized configuration for content.
        
        Args:
            total_duration: Total video duration in seconds
            slide_count: Number of slides
            
        Returns:
            Optimized VideoConfig instance
        """
        base_config = self.config_manager.create_default_config()
        return self.config_manager.optimize_config_for_content(base_config, total_duration, slide_count)


def create_video_synthesis_service(
    temp_dir: Optional[Path] = None,
    progress_callback: Optional[Callable] = None
) -> VideoSynthesisService:
    """
    Factory function to create video synthesis service.
    
    Args:
        temp_dir: Optional temporary directory
        progress_callback: Optional progress callback
        
    Returns:
        VideoSynthesisService instance
    """
    return VideoSynthesisService(temp_dir, progress_callback)