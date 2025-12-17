#!/usr/bin/env python3
"""
Video validation utilities for checking if video files are valid and complete.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class VideoValidator:
    """Utility class for validating video files."""
    
    @staticmethod
    def is_valid_video(video_path: Path, min_size_mb: float = 1.0, min_duration_seconds: float = 5.0) -> bool:
        """
        Check if a video file is valid and meets minimum requirements.
        
        Args:
            video_path: Path to the video file
            min_size_mb: Minimum file size in MB
            min_duration_seconds: Minimum duration in seconds
            
        Returns:
            True if video is valid, False otherwise
        """
        try:
            if not video_path.exists() or not video_path.is_file():
                return False
            
            # Check file size
            file_size_mb = video_path.stat().st_size / (1024 * 1024)
            if file_size_mb < min_size_mb:
                logger.debug(f"Video too small: {file_size_mb:.2f} MB < {min_size_mb} MB")
                return False
            
            # Check video properties using FFprobe
            video_info = VideoValidator.get_video_info(video_path)
            if not video_info:
                return False
            
            # Check duration
            duration = video_info.get('duration_seconds', 0)
            if duration < min_duration_seconds:
                logger.debug(f"Video too short: {duration:.2f}s < {min_duration_seconds}s")
                return False
            
            # Check if video has video stream
            if not video_info.get('has_video', False):
                logger.debug("No video stream found")
                return False
            
            # Check if video has audio stream
            if not video_info.get('has_audio', False):
                logger.debug("No audio stream found")
                return False
            
            logger.debug(f"Video validation passed: {video_path} ({file_size_mb:.2f} MB, {duration:.2f}s)")
            return True
            
        except Exception as e:
            logger.warning(f"Error validating video {video_path}: {e}")
            return False
    
    @staticmethod
    def get_video_info(video_path: Path, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get video information using FFprobe.
        
        Args:
            video_path: Path to the video file
            timeout: Timeout in seconds for FFprobe command
            
        Returns:
            Dictionary with video information or None if failed
        """
        try:
            # Use FFprobe to get video information
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                logger.warning(f"FFprobe failed for {video_path}: {result.stderr}")
                return None
            
            import json
            probe_data = json.loads(result.stdout)
            
            # Extract relevant information
            format_info = probe_data.get('format', {})
            streams = probe_data.get('streams', [])
            
            # Find video and audio streams
            video_streams = [s for s in streams if s.get('codec_type') == 'video']
            audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
            
            # Get duration (prefer format duration, fallback to video stream duration)
            duration = None
            if 'duration' in format_info:
                duration = float(format_info['duration'])
            elif video_streams and 'duration' in video_streams[0]:
                duration = float(video_streams[0]['duration'])
            
            # Get video properties
            video_info = {
                'duration_seconds': duration or 0,
                'has_video': len(video_streams) > 0,
                'has_audio': len(audio_streams) > 0,
                'file_size_bytes': int(format_info.get('size', 0)),
                'format_name': format_info.get('format_name', ''),
                'streams_count': len(streams)
            }
            
            # Add video stream info if available
            if video_streams:
                video_stream = video_streams[0]
                video_info.update({
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'video_codec': video_stream.get('codec_name', ''),
                    'frame_rate': video_stream.get('r_frame_rate', ''),
                    'bit_rate': int(video_stream.get('bit_rate', 0)) if video_stream.get('bit_rate') else 0
                })
            
            # Add audio stream info if available
            if audio_streams:
                audio_stream = audio_streams[0]
                video_info.update({
                    'audio_codec': audio_stream.get('codec_name', ''),
                    'sample_rate': int(audio_stream.get('sample_rate', 0)) if audio_stream.get('sample_rate') else 0,
                    'channels': int(audio_stream.get('channels', 0)) if audio_stream.get('channels') else 0
                })
            
            return video_info
            
        except subprocess.TimeoutExpired:
            logger.warning(f"FFprobe timeout for {video_path}")
            return None
        except Exception as e:
            logger.warning(f"Error getting video info for {video_path}: {e}")
            return None
    
    @staticmethod
    def estimate_expected_duration(audio_files: list[Path]) -> float:
        """
        Estimate expected video duration based on audio files.
        
        Args:
            audio_files: List of audio file paths
            
        Returns:
            Estimated duration in seconds
        """
        total_duration = 0.0
        
        for audio_file in audio_files:
            try:
                # Use FFprobe to get audio duration
                cmd = [
                    'ffprobe',
                    '-v', 'quiet',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(audio_file)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    duration = float(result.stdout.strip())
                    total_duration += duration
                else:
                    # Fallback: estimate based on file size (rough approximation)
                    file_size_mb = audio_file.stat().st_size / (1024 * 1024)
                    estimated_duration = file_size_mb * 8  # Very rough estimate: 8 seconds per MB
                    total_duration += estimated_duration
                    logger.debug(f"Using size-based duration estimate for {audio_file}: {estimated_duration:.2f}s")
                    
            except Exception as e:
                logger.warning(f"Error getting duration for {audio_file}: {e}")
                # Fallback: assume 30 seconds per audio file
                total_duration += 30.0
        
        return total_duration
    
    @staticmethod
    def should_skip_synthesis(
        output_path: Path,
        audio_files: list[Path],
        tolerance_factor: float = 0.8
    ) -> bool:
        """
        Determine if video synthesis should be skipped because a valid video already exists.
        
        Args:
            output_path: Path where the video would be created
            audio_files: List of audio files for duration estimation
            tolerance_factor: Minimum ratio of actual to expected duration (0.8 = 80%)
            
        Returns:
            True if synthesis should be skipped, False if it should proceed
        """
        if not output_path.exists():
            return False
        
        try:
            # Get expected duration from audio files
            expected_duration = VideoValidator.estimate_expected_duration(audio_files)
            min_expected_duration = expected_duration * tolerance_factor
            
            # Validate the existing video
            if VideoValidator.is_valid_video(
                output_path,
                min_size_mb=1.0,  # At least 1MB
                min_duration_seconds=min_expected_duration
            ):
                video_info = VideoValidator.get_video_info(output_path)
                if video_info:
                    actual_duration = video_info.get('duration_seconds', 0)
                    file_size_mb = video_info.get('file_size_bytes', 0) / (1024 * 1024)
                    
                    logger.info(f"Valid video exists: {output_path}")
                    logger.info(f"  Duration: {actual_duration:.2f}s (expected: {expected_duration:.2f}s)")
                    logger.info(f"  Size: {file_size_mb:.2f} MB")
                    
                    return True
            
            logger.info(f"Existing video invalid or too short, will regenerate: {output_path}")
            return False
            
        except Exception as e:
            logger.warning(f"Error checking existing video {output_path}: {e}")
            return False


def validate_video_file(video_path: str, min_size_mb: float = 1.0, min_duration_seconds: float = 5.0) -> bool:
    """
    Convenience function to validate a video file.
    
    Args:
        video_path: Path to the video file (string)
        min_size_mb: Minimum file size in MB
        min_duration_seconds: Minimum duration in seconds
        
    Returns:
        True if video is valid, False otherwise
    """
    return VideoValidator.is_valid_video(Path(video_path), min_size_mb, min_duration_seconds)


def should_skip_video_synthesis(output_path: str, audio_files: list[str], tolerance_factor: float = 0.8) -> bool:
    """
    Convenience function to check if video synthesis should be skipped.
    
    Args:
        output_path: Path where the video would be created (string)
        audio_files: List of audio file paths (strings)
        tolerance_factor: Minimum ratio of actual to expected duration
        
    Returns:
        True if synthesis should be skipped, False if it should proceed
    """
    return VideoValidator.should_skip_synthesis(
        Path(output_path),
        [Path(f) for f in audio_files],
        tolerance_factor
    )