"""FFmpeg video processing engine for video synthesis."""

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING

# Direct FFmpeg implementation - no python wrapper dependencies

from core.domain.video_synthesis import (
    VideoConfig, SlideVideoSegment, VideoProcessingError
)
from services.video_synthesis.video_combine_helpers import build_normalized_concat_command

if TYPE_CHECKING:
    from .file_manager import VideoFileManager

logger = logging.getLogger(__name__)


class FFmpegVideoProcessor:
    """Core video processing engine using direct FFmpeg subprocess calls."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        """
        Initialize FFmpeg video processor.
        
        Args:
            temp_dir: Optional temporary directory for intermediate files
        """
        self.temp_dir = temp_dir or Path(tempfile.gettempdir())
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def create_video_segment(
        self,
        segment: SlideVideoSegment,
        config: VideoConfig,
        temp_dir: Path,
        file_manager: Optional['VideoFileManager'] = None
    ) -> Path:
        """
        Convert a slide image and audio into a video segment.
        
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
            logger.debug(f"Creating video segment for slide {segment.slide_index}")
            
            # Check cache first if file manager is provided
            if file_manager and file_manager.enable_cache:
                config_dict = self._build_cache_config(config)
                cache_key = file_manager.generate_segment_cache_key(
                    segment.image_path, segment.audio_path, config_dict, segment.slide_index
                )
                
                cached_segment = file_manager.get_cached_segment(cache_key, config.output_format)
                if cached_segment:
                    # Use cached segment directly - no need to copy to temp
                    segment.temp_video_path = cached_segment
                    
                    logger.info(f"Using cached segment for slide {segment.slide_index}: {cached_segment}")
                    return cached_segment
            
            # Generate output filename
            segment_filename = f"segment_{segment.slide_index:03d}.{config.output_format}"
            segment_output_path = temp_dir / segment_filename
            
            # Ensure the output directory exists before FFmpeg tries to write
            # This is critical - FFmpeg will fail if the directory doesn't exist
            segment_output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use direct FFmpeg command for segment creation
            logger.debug(f"Creating segment {segment.slide_index} using direct FFmpeg")
            
            # Build FFmpeg command
            cmd = [
                "ffmpeg", "-y",  # Overwrite output
                "-loop", "1", "-i", str(segment.image_path),  # Loop the image
                "-i", str(segment.audio_path),  # Audio input
                "-c:v", config.video_codec,  # Video codec
                "-c:a", config.audio_codec,  # Audio codec
                "-shortest",  # Stop when shortest input ends (audio)
                "-pix_fmt", "yuv420p",  # Pixel format for compatibility
                "-r", str(config.fps),  # Frame rate
                "-vf", f"scale={config.resolution[0]}:{config.resolution[1]}:force_original_aspect_ratio=decrease,pad={config.resolution[0]}:{config.resolution[1]}:(ow-iw)/2:(oh-ih)/2:black",  # Scale and pad
                "-b:v", config.video_bitrate,  # Video bitrate
                "-b:a", config.audio_bitrate,  # Audio bitrate
                str(segment_output_path)  # Output file
            ]
            
            logger.debug(f"FFmpeg segment command: {' '.join(cmd[:10])}...")  # Log first part of command
            
            try:
                # Timeout based on audio duration (with minimum and maximum bounds)
                timeout_seconds = max(30, min(300, segment.duration_seconds * 3 + 30))  # 3x audio duration + 30s buffer
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )
                
                if result.returncode == 0:
                    logger.debug(f"Segment {segment.slide_index} created successfully")
                else:
                    logger.error(f"FFmpeg segment creation failed for slide {segment.slide_index}")
                    logger.error(f"Return code: {result.returncode}")
                    logger.error(f"Stderr: {result.stderr}")
                    logger.error(f"Stdout: {result.stdout}")
                    raise VideoProcessingError(f"FFmpeg segment creation failed for slide {segment.slide_index}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error(f"FFmpeg segment creation timed out after {timeout_seconds} seconds for slide {segment.slide_index}")
                raise VideoProcessingError(f"FFmpeg segment creation timed out after {timeout_seconds} seconds for slide {segment.slide_index}")
            except FileNotFoundError:
                logger.error("FFmpeg not found in PATH")
                raise VideoProcessingError("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
            except Exception as e:
                logger.error(f"Unexpected error creating segment {segment.slide_index}: {e}")
                raise VideoProcessingError(f"Failed to create segment {segment.slide_index}: {e}")
            
            # Verify output file was created
            if not segment_output_path.exists():
                raise VideoProcessingError(f"Failed to create video segment: {segment_output_path}")
            
            # Cache the segment if file manager is provided
            if file_manager and file_manager.enable_cache:
                try:
                    cached_path = file_manager.cache_segment(segment_output_path, cache_key)
                    # Use the cached path as the segment path
                    segment.temp_video_path = cached_path
                    logger.debug(f"Successfully cached and using segment: {cached_path}")
                    return cached_path
                except Exception as e:
                    logger.warning(f"Failed to cache segment for slide {segment.slide_index}: {e}")
            
            # Update segment with temp video path
            segment.temp_video_path = segment_output_path
            
            logger.debug(f"Successfully created video segment: {segment_output_path}")
            return segment_output_path
            

        except Exception as e:
            error_msg = f"Failed to create video segment for slide {segment.slide_index}: {e}"
            logger.error(error_msg)
            raise VideoProcessingError(error_msg) from e

    def _build_cache_config(self, config: VideoConfig) -> Dict[str, Any]:
        """Build the deterministic cache config used for segment keys."""
        return {
            "resolution": config.resolution,
            "fps": config.fps,
            "video_codec": config.video_codec,
            "audio_codec": config.audio_codec,
            "video_bitrate": config.video_bitrate,
            "audio_bitrate": config.audio_bitrate,
            "output_format": config.output_format,
            "fade_duration": config.fade_duration,
        }
    

    
    def _get_format_specific_options(self, config: VideoConfig) -> Dict[str, Any]:
        """
        Get format-specific encoding options.
        
        Args:
            config: Video configuration
            
        Returns:
            Dictionary of format-specific options
        """
        options = {}
        
        if config.output_format == 'mp4':
            options.update({
                'movflags': '+faststart',  # Enable fast start for web playback
                'preset': 'medium',        # H.264 encoding preset
                'crf': '23'               # Constant rate factor for quality
            })
        elif config.output_format == 'webm':
            options.update({
                'deadline': 'good',       # VP8/VP9 encoding quality
                'cpu-used': '2'          # Encoding speed vs quality tradeoff
            })
        
        return options
    
    def concatenate_segments(
        self,
        segments: List[SlideVideoSegment],
        config: VideoConfig,
        output_path: Path,
        temp_dir: Path
    ) -> Path:
        """
        Concatenate multiple video segments into final video.
        
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
        try:
            logger.info(f"Concatenating {len(segments)} video segments")
            
            if not segments:
                raise VideoProcessingError("No video segments to concatenate")
            
            # Verify all segments have temp video paths
            for i, segment in enumerate(segments):
                if not segment.temp_video_path or not segment.temp_video_path.exists():
                    raise VideoProcessingError(f"Missing video segment file for slide {i}")
            
            if len(segments) == 1:
                # Single segment - just copy/move to output
                single_segment = segments[0]
                logger.debug("Single segment - copying to output")
                
                # Use direct FFmpeg command for single segment
                logger.info("Processing single segment...")
                
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(single_segment.temp_video_path),
                    "-c", "copy",  # Copy without re-encoding for speed
                    str(output_path)
                ]
                
                # Add format-specific options if needed
                format_options = self._get_format_specific_options(config)
                if format_options and not config.output_format == 'mp4':  # Skip for MP4 with copy
                    for key, value in format_options.items():
                        cmd.extend([f"-{key}", str(value)])
                
                try:
                    timeout_seconds = max(60, single_segment.duration_seconds * 2 + 30)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
                    
                    if result.returncode == 0:
                        logger.info("Single segment processing completed")
                    else:
                        logger.error(f"Single segment processing failed: {result.stderr}")
                        raise VideoProcessingError(f"Single segment processing failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    raise VideoProcessingError(f"Single segment processing timed out after {timeout_seconds} seconds")
            else:
                # Multiple segments - concatenate with optional transitions
                if config.fade_duration > 0:
                    self._concatenate_with_transitions(segments, config, output_path, temp_dir)
                else:
                    self._concatenate_simple(segments, config, output_path, temp_dir)
            
            # Verify output file was created
            if not output_path.exists():
                raise VideoProcessingError(f"Failed to create final video: {output_path}")
            
            logger.info(f"Successfully created final video: {output_path}")
            return output_path
            

        except Exception as e:
            error_msg = f"Failed to concatenate video segments: {e}"
            logger.error(error_msg)
            raise VideoProcessingError(error_msg) from e

    def concatenate_video_files(
        self,
        video_paths: List[Path],
        config: VideoConfig,
        output_path: Path,
        temp_dir: Path,
    ) -> Path:
        """Concatenate pre-rendered video files in order."""
        try:
            if not video_paths:
                raise VideoProcessingError("No video files to concatenate")

            for video_path in video_paths:
                if not video_path.exists():
                    raise VideoProcessingError(f"Missing video file: {video_path}")

            if len(video_paths) == 1:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(video_paths[0], output_path)
                return output_path

            output_path.parent.mkdir(parents=True, exist_ok=True)
            timeout_seconds = max(900, len(video_paths) * 60)
            cmd = build_normalized_concat_command(video_paths, output_path, config)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds, cwd=temp_dir)
            if result.returncode != 0:
                raise VideoProcessingError(f"FFmpeg concatenation failed: {result.stderr}")

            if not output_path.exists():
                raise VideoProcessingError(f"Failed to create final video: {output_path}")

            return output_path
        except Exception as e:
            error_msg = f"Failed to concatenate video files: {e}"
            logger.error(error_msg)
            raise VideoProcessingError(error_msg) from e
    
    def _concatenate_simple(
        self,
        segments: List[SlideVideoSegment],
        config: VideoConfig,
        output_path: Path,
        temp_dir: Path
    ) -> None:
        """
        Simple concatenation without transitions.
        
        Args:
            segments: List of video segments
            config: Video configuration
            output_path: Output video path
            temp_dir: Temporary directory
        """
        # Try concat demuxer first (fastest), fallback to filter_complex if it fails
        try:
            self._concatenate_with_demuxer(segments, config, output_path, temp_dir)
        except Exception as e:
            logger.warning(f"Concat demuxer failed: {e}")
            logger.info("Falling back to filter_complex concatenation...")
            try:
                self._concatenate_with_filter_complex(segments, config, output_path, temp_dir)
            except Exception as e2:
                logger.error(f"Filter_complex concatenation also failed: {e2}")
                logger.warning("All concatenation methods failed, creating emergency single-segment video")
                self._create_emergency_video(segments, config, output_path, temp_dir)
    
    def _concatenate_with_demuxer(
        self,
        segments: List[SlideVideoSegment],
        config: VideoConfig,
        output_path: Path,
        temp_dir: Path
    ) -> None:
        """Concatenate using direct FFmpeg command (most reliable method)."""
        # Check if we have too many segments for simple concatenation
        if len(segments) > 50:
            logger.warning(f"Large number of segments ({len(segments)}), using chunked concatenation")
            self._concatenate_chunked(segments, config, output_path, temp_dir)
            return
        
        # Create concat file list
        concat_file_path = temp_dir / "concat_list.txt"
        
        with open(concat_file_path, 'w') as f:
            for segment in segments:
                f.write(f"file '{segment.temp_video_path.absolute()}'\n")
        
        logger.info(f"Starting direct FFmpeg concatenation of {len(segments)} segments...")
        logger.debug(f"Concat file contents:")
        with open(concat_file_path, 'r') as f:
            for i, line in enumerate(f.readlines()[:5]):  # Show first 5 lines
                logger.debug(f"  {i+1}: {line.strip()}")
            if len(segments) > 5:
                logger.debug(f"  ... and {len(segments) - 5} more files")
        
        # Use direct FFmpeg command (proven to work reliably)
        cmd = [
            "ffmpeg", "-y",  # Overwrite output
            "-f", "concat",  # Use concat demuxer
            "-safe", "0",    # Allow absolute paths
            "-i", str(concat_file_path),  # Input concat file
            "-c", "copy",    # Copy streams without re-encoding (fastest)
            str(output_path)  # Output file
        ]
        
        # Add format-specific options if needed
        format_options = self._get_format_specific_options(config)
        if format_options and not config.output_format == 'mp4':  # Skip for MP4 with copy
            for key, value in format_options.items():
                cmd.extend([f"-{key}", str(value)])
        
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run with timeout and error handling
        try:
            timeout_seconds = max(60, len(segments) * 5)  # At least 60s, or 5s per segment
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=temp_dir  # Run in temp directory
            )
            
            if result.returncode == 0:
                logger.info("Direct FFmpeg concatenation completed successfully")
            else:
                # Log detailed error information
                logger.error(f"FFmpeg concatenation failed with return code {result.returncode}")
                logger.error(f"FFmpeg stderr: {result.stderr}")
                logger.error(f"FFmpeg stdout: {result.stdout}")
                
                # Log the concat file for debugging
                logger.error("Concat file contents (first 10 lines):")
                with open(concat_file_path, 'r') as f:
                    for i, line in enumerate(f.readlines()[:10]):
                        logger.error(f"  {i+1}: {line.strip()}")
                
                raise VideoProcessingError(f"FFmpeg concatenation failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg concatenation timed out after {timeout_seconds} seconds")
            raise VideoProcessingError(f"FFmpeg concatenation timed out after {timeout_seconds} seconds")
        except FileNotFoundError:
            logger.error("FFmpeg not found in PATH")
            raise VideoProcessingError("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
        except Exception as e:
            logger.error(f"Unexpected error during FFmpeg concatenation: {e}")
            raise VideoProcessingError(f"FFmpeg concatenation failed: {e}")
        finally:
            # Clean up concat file
            concat_file_path.unlink(missing_ok=True)
    
    def _concatenate_chunked(
        self,
        segments: List[SlideVideoSegment],
        config: VideoConfig,
        output_path: Path,
        temp_dir: Path
    ) -> None:
        """
        Concatenate large numbers of segments by processing in chunks.
        
        This method splits large segment lists into smaller chunks, concatenates
        each chunk separately, then concatenates the chunk results.
        """
        logger.info(f"Starting chunked concatenation of {len(segments)} segments")
        
        chunk_size = 20  # Process 20 segments at a time
        chunks = [segments[i:i + chunk_size] for i in range(0, len(segments), chunk_size)]
        
        logger.info(f"Split into {len(chunks)} chunks of up to {chunk_size} segments each")
        
        chunk_outputs = []
        
        try:
            # Process each chunk
            for i, chunk in enumerate(chunks):
                chunk_output = temp_dir / f"chunk_{i:03d}.{config.output_format}"
                logger.info(f"Processing chunk {i+1}/{len(chunks)} with {len(chunk)} segments")
                
                # Create concat file for this chunk
                chunk_concat_file = temp_dir / f"chunk_{i:03d}_concat.txt"
                with open(chunk_concat_file, 'w') as f:
                    for segment in chunk:
                        f.write(f"file '{segment.temp_video_path.absolute()}'\n")
                
                # Concatenate this chunk using direct FFmpeg
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(chunk_concat_file),
                    "-c", "copy",  # Copy without re-encoding
                    str(chunk_output)
                ]
                
                try:
                    timeout_seconds = max(60, len(chunk) * 10)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
                    
                    if result.returncode == 0:
                        chunk_outputs.append(chunk_output)
                        logger.info(f"Chunk {i+1} completed successfully")
                    else:
                        logger.error(f"Chunk {i+1} concatenation failed: {result.stderr}")
                        raise VideoProcessingError(f"Chunk {i+1} concatenation failed: {result.stderr}")
                    
                except subprocess.TimeoutExpired:
                    raise VideoProcessingError(f"Chunk {i+1} concatenation timed out")
                finally:
                    # Clean up chunk concat file
                    chunk_concat_file.unlink(missing_ok=True)
            
            # Now concatenate all chunks into final output
            logger.info(f"Concatenating {len(chunk_outputs)} chunks into final video")
            
            if len(chunk_outputs) == 1:
                # Only one chunk, just copy it
                shutil.copy2(chunk_outputs[0], output_path)
            else:
                # Multiple chunks, concatenate them
                final_concat_file = temp_dir / "final_concat.txt"
                with open(final_concat_file, 'w') as f:
                    for chunk_output in chunk_outputs:
                        f.write(f"file '{chunk_output.absolute()}'\n")
                
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(final_concat_file),
                    "-c", "copy",  # Copy without re-encoding
                    str(output_path)
                ]
                
                # Add format-specific options if needed
                format_options = self._get_format_specific_options(config)
                if format_options and not config.output_format == 'mp4':  # Skip for MP4 with copy
                    for key, value in format_options.items():
                        cmd.extend([f"-{key}", str(value)])
                
                try:
                    timeout_seconds = max(120, len(chunk_outputs) * 30)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
                    
                    if result.returncode == 0:
                        logger.info("Final concatenation completed successfully")
                    else:
                        logger.error(f"Final concatenation failed: {result.stderr}")
                        raise VideoProcessingError(f"Final concatenation failed: {result.stderr}")
                    
                except subprocess.TimeoutExpired:
                    raise VideoProcessingError("Final concatenation timed out")
                finally:
                    final_concat_file.unlink(missing_ok=True)
            
        finally:
            # Clean up chunk output files
            for chunk_output in chunk_outputs:
                chunk_output.unlink(missing_ok=True)
    
    def _create_emergency_video(
        self,
        segments: List[SlideVideoSegment],
        config: VideoConfig,
        output_path: Path,
        temp_dir: Path
    ) -> None:
        """
        Create an emergency video using just the first segment when all else fails.
        
        This is a last resort to provide some output rather than complete failure.
        """
        logger.warning("Creating emergency video with first segment only")
        
        if not segments:
            raise VideoProcessingError("No segments available for emergency video")
        
        first_segment = segments[0]
        if not first_segment.temp_video_path or not first_segment.temp_video_path.exists():
            raise VideoProcessingError("First segment file not available for emergency video")
        
        try:
            # Just copy the first segment as the output
            shutil.copy2(first_segment.temp_video_path, output_path)
            logger.warning(f"Emergency video created with only first segment: {output_path}")
            
        except Exception as e:
            raise VideoProcessingError(f"Failed to create emergency video: {e}")
    
    def _concatenate_with_filter_complex(
        self,
        segments: List[SlideVideoSegment],
        config: VideoConfig,
        output_path: Path,
        temp_dir: Path
    ) -> None:
        """Fallback concatenation using direct FFmpeg filter_complex command."""
        logger.info(f"Starting direct FFmpeg filter_complex concatenation of {len(segments)} segments...")
        
        # Build FFmpeg command with filter_complex
        cmd = ["ffmpeg", "-y"]
        
        # Add all input files
        for segment in segments:
            cmd.extend(["-i", str(segment.temp_video_path)])
        
        # Build filter_complex string
        if len(segments) == 1:
            # Single input, just copy
            cmd.extend(["-c", "copy", str(output_path)])
        else:
            # Multiple inputs, use concat filter
            filter_complex = f"concat=n={len(segments)}:v=1:a=1[outv][outa]"
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", config.video_codec,
                "-c:a", config.audio_codec,
                str(output_path)
            ])
        
        # Run with timeout
        try:
            timeout_seconds = max(120, len(segments) * 15)  # At least 2 minutes, or 15s per segment
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            
            if result.returncode == 0:
                logger.info("Direct FFmpeg filter_complex concatenation completed successfully")
            else:
                logger.error(f"FFmpeg filter_complex concatenation failed: {result.stderr}")
                raise VideoProcessingError(f"FFmpeg filter_complex concatenation failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise VideoProcessingError(f"FFmpeg filter_complex concatenation timed out after {timeout_seconds} seconds")
        except FileNotFoundError:
            raise VideoProcessingError("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
        except Exception as e:
            raise VideoProcessingError(f"FFmpeg filter_complex concatenation failed: {e}")
    
    def _concatenate_with_transitions(
        self,
        segments: List[SlideVideoSegment],
        config: VideoConfig,
        output_path: Path,
        temp_dir: Path
    ) -> None:
        """
        Concatenation with fade transitions between segments using direct FFmpeg.
        
        Args:
            segments: List of video segments
            config: Video configuration
            output_path: Output video path
            temp_dir: Temporary directory
        """
        logger.debug(f"Concatenating with {config.fade_duration}s fade transitions using direct FFmpeg")
        
        # For now, fall back to simple concatenation since transitions are complex
        # TODO: Implement direct FFmpeg crossfade transitions
        logger.warning("Fade transitions not yet implemented with direct FFmpeg, using simple concatenation")
        self._concatenate_simple(segments, config, output_path, temp_dir)
    
    def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """
        Get information about a video file using direct FFmpeg probe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary containing video information
            
        Raises:
            VideoProcessingError: If video info extraction fails
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10  # Shorter timeout for video info - this should be fast
            )
            
            if result.returncode != 0:
                raise VideoProcessingError(f"FFprobe failed for video file {video_path}: {result.stderr}")
            
            probe_result = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            audio_stream = None
            
            for stream in probe_result.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            format_info = probe_result.get('format', {})
            
            info = {
                'duration_seconds': float(format_info.get('duration', 0)),
                'file_size_bytes': int(format_info.get('size', 0)),
                'format_name': format_info.get('format_name', 'unknown'),
                'bit_rate': int(format_info.get('bit_rate', 0))
            }
            
            if video_stream:
                # Handle frame rate calculation safely
                fps = 0
                r_frame_rate = video_stream.get('r_frame_rate', '0/1')
                if '/' in r_frame_rate:
                    try:
                        num, den = r_frame_rate.split('/')
                        fps = float(num) / float(den) if float(den) != 0 else 0
                    except:
                        fps = 0
                
                info.update({
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'video_codec': video_stream.get('codec_name', 'unknown'),
                    'fps': fps,
                    'video_bitrate': int(video_stream.get('bit_rate', 0))
                })
            
            if audio_stream:
                info.update({
                    'audio_codec': audio_stream.get('codec_name', 'unknown'),
                    'sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'channels': int(audio_stream.get('channels', 0)),
                    'audio_bitrate': int(audio_stream.get('bit_rate', 0))
                })
            
            return info
            
        except subprocess.TimeoutExpired:
            raise VideoProcessingError(f"Video info extraction timed out for file: {video_path}")
        except FileNotFoundError:
            raise VideoProcessingError("FFprobe not found. Please install FFmpeg and ensure it's in your PATH.")
        except json.JSONDecodeError as e:
            raise VideoProcessingError(f"Failed to parse FFprobe output for {video_path}: {e}")
        except Exception as e:
            error_msg = f"Failed to get video info for {video_path}: {e}"
            logger.error(error_msg)
            raise VideoProcessingError(error_msg) from e