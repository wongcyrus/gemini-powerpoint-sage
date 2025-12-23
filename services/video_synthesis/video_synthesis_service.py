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
from config.cleanup_config import CleanupConfig

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
        
        # Derive audio directory from first audio file for cache location
        audio_dir = request.audio_files[0].parent if request.audio_files else None
        
        # Initialize file manager with audio_dir for presentation-specific caching
        file_manager = VideoFileManager(self.temp_dir, operation_id, audio_dir=audio_dir)
        
        try:
            logger.info(f"Starting video synthesis: {operation_id}")
            
            # Check available disk space before starting
            self._check_disk_space(request, file_manager)
            
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
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Progress tracker timeout")
                
                # Set a 5-second timeout for progress tracker completion
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)
                
                progress_tracker.mark_completed(final_output, file_size, video_duration)
                
                # Cancel the alarm
                signal.alarm(0)
                
            except (Exception, TimeoutError) as e:
                # Cancel the alarm in case of exception
                try:
                    signal.alarm(0)
                except:
                    pass
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
            # Ensure cleanup happens immediately to free disk space
            try:
                logger.info("Ensuring cleanup of temporary files to prevent disk space issues")
                file_manager.cleanup(force=True)
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")
    
    def _check_disk_space(self, request: VideoSynthesisRequest, file_manager: VideoFileManager) -> None:
        """
        Check available disk space before starting video synthesis.
        
        Args:
            request: Video synthesis request
            file_manager: File manager instance
            
        Raises:
            VideoSynthesisError: If insufficient disk space
        """
        try:
            import os
            
            # Check temp directory space
            temp_dir = file_manager.temp_dir
            statvfs = os.statvfs(temp_dir)
            available_bytes = statvfs.f_frsize * statvfs.f_bavail
            available_gb = available_bytes / (1024**3)
            
            # More accurate space estimation based on actual file sizes
            total_audio_size = sum(f.stat().st_size for f in request.audio_files if f.exists())
            total_image_size = sum(f.stat().st_size for f in request.slide_images if f.exists())
            
            # Estimate space needed:
            # - Audio files: already counted
            # - Video segments: ~3x audio size (video encoding overhead)
            # - Final video: ~1x audio size (compressed)
            # - Working space: ~1x for intermediate files
            estimated_space_needed = total_audio_size * 5  # Conservative estimate
            estimated_gb = estimated_space_needed / (1024**3)
            
            logger.info(f"Disk space check: {available_gb:.2f} GB available")
            logger.info(f"Content size: audio {total_audio_size/(1024**3):.2f} GB, images {total_image_size/(1024**3):.2f} GB")
            logger.info(f"Estimated space needed: ~{estimated_gb:.2f} GB")
            
            # For very large presentations (>200 slides), be more conservative
            if len(request.slide_images) > 200:
                safety_multiplier = 1.5
                estimated_space_needed = int(estimated_space_needed * safety_multiplier)
                estimated_gb = estimated_space_needed / (1024**3)
                logger.warning(f"Large presentation ({len(request.slide_images)} slides) - using conservative estimate: {estimated_gb:.2f} GB")
            
            # Warn if less than 3GB available or less than 2x estimated need
            if available_gb < 3.0:
                logger.warning(f"Low disk space: only {available_gb:.2f} GB available in {temp_dir}")
            elif available_bytes < (estimated_space_needed * 2):
                logger.warning(f"Tight disk space: {available_gb:.2f} GB available, {estimated_gb:.2f} GB estimated needed")
            
            # Error if less than 1.5GB available or less than 1.2x estimated need
            if available_gb < 1.5:
                raise VideoSynthesisError(f"Insufficient disk space: only {available_gb:.2f} GB available in {temp_dir}")
            elif available_bytes < (estimated_space_needed * 1.2):
                raise VideoSynthesisError(f"Insufficient disk space: {available_gb:.2f} GB available, {estimated_gb:.2f} GB estimated needed")
                
        except Exception as e:
            if isinstance(e, VideoSynthesisError):
                raise
            logger.warning(f"Could not check disk space: {e}")

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
                    # Extract slide number from filename for proper indexing
                    slide_number = self._extract_slide_number_from_files(image_path, audio_path)
                    
                    # Create segment with proper slide number (not loop index)
                    segment = SlideVideoSegment.from_files(slide_number, image_path, audio_path)
                    segments.append(segment)
                    
                    logger.debug(f"Analyzed slide {slide_number}: {segment.duration_seconds:.3f}s")
                    
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
    
    def _extract_slide_number_from_files(self, image_path: Path, audio_path: Path) -> int:
        """
        Extract slide number from image and audio filenames.
        
        Args:
            image_path: Path to slide image (e.g., slide_5_reimagined.png)
            audio_path: Path to audio file (e.g., slide_5_abc123.mp3)
            
        Returns:
            Slide number extracted from filenames
            
        Raises:
            ValueError: If slide numbers don't match or can't be extracted
        """
        import re
        
        # Extract slide number from image filename
        img_match = re.search(r'slide_(\d+)', image_path.name)
        if not img_match:
            raise ValueError(f"Cannot extract slide number from image filename: {image_path.name}")
        img_slide_num = int(img_match.group(1))
        
        # Extract slide number from audio filename  
        audio_match = re.search(r'slide_(\d+)', audio_path.name)
        if not audio_match:
            raise ValueError(f"Cannot extract slide number from audio filename: {audio_path.name}")
        audio_slide_num = int(audio_match.group(1))
        
        # Verify they match
        if img_slide_num != audio_slide_num:
            raise ValueError(
                f"Slide number mismatch: image has slide {img_slide_num}, "
                f"audio has slide {audio_slide_num}"
            )
        
        return img_slide_num
    
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
            
            # For very large presentations, process in chunks to manage memory
            if CleanupConfig.should_use_chunked_processing(len(segments)):
                logger.info(f"Large presentation detected ({len(segments)} slides) - using chunked processing")
                return self._create_video_segments_chunked(segments, config, file_manager, progress_tracker)
            
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

    def _create_video_segments_chunked(
        self,
        segments: list[SlideVideoSegment],
        config: VideoConfig,
        file_manager: VideoFileManager,
        progress_tracker: VideoProgressTracker
    ) -> list[SlideVideoSegment]:
        """
        Create video segments in chunks for large presentations to manage memory and disk space.
        
        Args:
            segments: List of slide video segments
            config: Video configuration
            file_manager: File manager
            progress_tracker: Progress tracker
            
        Returns:
            List of segments with temp video paths
        """
        chunk_size = CleanupConfig.get_chunk_size()  # Use configurable chunk size
        chunks = [segments[i:i + chunk_size] for i in range(0, len(segments), chunk_size)]
        
        logger.info(f"Processing {len(segments)} segments in {len(chunks)} chunks of {chunk_size}")
        
        # Create segments directory
        segments_dir = file_manager.create_segment_temp_dir()
        
        # Initialize FFmpeg processor
        ffmpeg_processor = FFmpegVideoProcessor(segments_dir)
        
        processed_segments = []
        
        for chunk_idx, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {chunk_idx + 1}/{len(chunks)} ({len(chunk)} segments)")
            
            chunk_processed = []
            
            for i, segment in enumerate(chunk):
                global_idx = chunk_idx * chunk_size + i
                progress_tracker.update_slide_progress(
                    global_idx, ProcessingStage.CREATING_SEGMENTS,
                    f"Creating video segment {global_idx+1}/{len(segments)}: {segment.image_path.name}"
                )
                
                try:
                    # Create video segment with caching support
                    segment_path = ffmpeg_processor.create_video_segment(segment, config, segments_dir, file_manager)
                    
                    # Update segment with temp path
                    segment.temp_video_path = segment_path
                    chunk_processed.append(segment)
                    
                    logger.debug(f"Created video segment {global_idx+1}: {segment_path}")
                    
                except Exception as e:
                    progress_tracker.report_error(e, global_idx)
                    raise VideoProcessingError(f"Failed to create video segment {global_idx+1}: {e}") from e
            
            processed_segments.extend(chunk_processed)
            
            # After each chunk, do a mini cleanup to free space
            if chunk_idx < len(chunks) - 1:  # Don't cleanup on last chunk
                logger.info(f"Chunk {chunk_idx + 1} completed, performing mini cleanup...")
                try:
                    file_manager._cleanup_temp_files_immediately()
                except Exception as e:
                    logger.warning(f"Mini cleanup failed: {e}")
        
        logger.info(f"Successfully created {len(processed_segments)} video segments using chunked processing")
        return processed_segments
    
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
    
    def combine_videos(
        self,
        video_paths: list[Path],
        output_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> VideoSynthesisResult:
        """
        Combine multiple video files into a single video using MoviePy.
        
        Args:
            video_paths: List of paths to video files to combine
            output_path: Path for the output combined video
            progress_callback: Optional progress callback
            
        Returns:
            VideoSynthesisResult with operation outcome
        """
        # Use FFmpeg for video combining (much faster than MoviePy)
        try:
            import subprocess
        except ImportError:
            raise VideoSynthesisError("subprocess module not available")
        
        start_time = time.time()
        operation_id = f"video_combine_{int(start_time)}"
        
        # Use provided callback or instance callback
        callback = progress_callback or self.progress_callback
        
        try:
            logger.info(f"Starting video combination: {operation_id}")
            logger.info(f"Combining {len(video_paths)} videos into {output_path}")
            
            if callback:
                callback({
                    'operation_id': operation_id,
                    'stage': 'loading',
                    'message': f'Loading {len(video_paths)} video files',
                    'progress': 0
                })
            
            # Validate input files
            for i, video_path in enumerate(video_paths):
                if not video_path.exists():
                    raise FileValidationError(f"Video file not found: {video_path}")
                if not video_path.is_file():
                    raise FileValidationError(f"Path is not a file: {video_path}")
            
            # Get total duration using FFmpeg
            total_duration = 0
            
            for i, video_path in enumerate(video_paths):
                if callback:
                    callback({
                        'operation_id': operation_id,
                        'stage': 'analyzing',
                        'message': f'Analyzing video {i+1}/{len(video_paths)}: {video_path.name}',
                        'progress': (i / len(video_paths)) * 20  # 20% for analysis
                    })
                
                try:
                    # Get video duration using FFprobe
                    result = subprocess.run([
                        'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1', str(video_path)
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        duration = float(result.stdout.strip())
                        total_duration += duration
                        logger.debug(f"Video {i+1}: {video_path.name} ({duration:.2f}s)")
                    else:
                        raise VideoProcessingError(f"Failed to get duration for {video_path}")
                        
                except Exception as e:
                    raise VideoProcessingError(f"Failed to analyze video {video_path}: {e}")
            
            if callback:
                callback({
                    'operation_id': operation_id,
                    'stage': 'concatenating',
                    'message': f'Concatenating {len(video_paths)} video files with FFmpeg',
                    'progress': 40
                })
            
            # Concatenate videos using FFmpeg
            logger.info(f"Concatenating {len(video_paths)} videos (total duration: {total_duration:.2f}s)")
            
            # Create temporary concat file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                concat_file = Path(f.name)
                for video_path in video_paths:
                    f.write(f"file '{video_path.absolute()}'\n")
            
            try:
                if callback:
                    callback({
                        'operation_id': operation_id,
                        'stage': 'writing',
                        'message': f'Writing combined video to {output_path.name}',
                        'progress': 60
                    })
                
                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Use FFmpeg concat demuxer (fastest method)
                cmd = [
                    'ffmpeg', '-y',  # Overwrite output
                    '-f', 'concat',  # Use concat demuxer
                    '-safe', '0',    # Allow absolute paths
                    '-i', str(concat_file),  # Input concat file
                    '-c', 'copy',    # Copy streams without re-encoding (fastest!)
                    str(output_path)  # Output file
                ]
                
                logger.info(f"Running FFmpeg: {' '.join(cmd[:6])}...")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=max(300, len(video_paths) * 10)  # 5 min minimum, 10s per video
                )
                
                if result.returncode != 0:
                    raise VideoProcessingError(f"FFmpeg concatenation failed: {result.stderr}")
                
                logger.info(f"FFmpeg concatenation completed successfully")
                
            finally:
                # Clean up concat file
                concat_file.unlink(missing_ok=True)
            
            # Calculate final statistics
            processing_time = time.time() - start_time
            file_size = output_path.stat().st_size
            
            if callback:
                callback({
                    'operation_id': operation_id,
                    'stage': 'completed',
                    'message': f'Video combination completed: {output_path.name}',
                    'progress': 100
                })
            
            # Create success result
            result = VideoSynthesisResult.success_result(
                output_path=output_path,
                duration_seconds=total_duration,
                file_size_bytes=file_size,
                processing_time_seconds=processing_time,
                slides_processed=len(video_paths),
                metadata={
                    'operation_id': operation_id,
                    'input_videos': [str(p) for p in video_paths],
                    'combination_method': 'ffmpeg_concat'
                }
            )
            
            logger.info(f"Video combination completed successfully: {output_path}")
            return result
            
        except Exception as e:
            # Clean up concat file if it exists
            try:
                if 'concat_file' in locals():
                    concat_file.unlink(missing_ok=True)
            except:
                pass  # Ignore cleanup errors
            
            processing_time = time.time() - start_time
            
            if callback:
                callback({
                    'operation_id': operation_id,
                    'stage': 'failed',
                    'message': f'Video combination failed: {str(e)}',
                    'progress': 0
                })
            
            # Create failure result
            result = VideoSynthesisResult.failure_result(
                error_message=str(e),
                processing_time_seconds=processing_time,
                slides_processed=0,
                metadata={
                    'operation_id': operation_id,
                    'error_type': type(e).__name__,
                    'input_videos': [str(p) for p in video_paths] if 'video_paths' in locals() else []
                }
            )
            
            logger.error(f"Video combination failed: {e}")
            return result


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