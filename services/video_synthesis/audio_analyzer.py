"""Audio analysis service for video synthesis."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    ffmpeg = None

from core.domain.video_synthesis import AudioAnalysisError

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Service for analyzing audio files for video synthesis."""
    
    def __init__(self):
        """Initialize audio analyzer."""
        self.supported_formats = {'.mp3'}
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Extract duration from audio file using ffmpeg probe.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds with millisecond precision
            
        Raises:
            AudioAnalysisError: If duration extraction fails
        """
        try:
            logger.debug(f"Extracting duration from audio file: {audio_path}")
            
            if not FFMPEG_AVAILABLE:
                raise AudioAnalysisError("ffmpeg-python is not available. Please install it to use audio analysis.")
            
            # Validate file exists
            if not audio_path.exists():
                raise AudioAnalysisError(f"Audio file not found: {audio_path}")
            
            # Validate file format
            if audio_path.suffix.lower() not in self.supported_formats:
                raise AudioAnalysisError(
                    f"Unsupported audio format: {audio_path.suffix}. "
                    f"Supported formats: {', '.join(self.supported_formats)}"
                )
            
            # Use ffmpeg probe to get file information
            probe_result = ffmpeg.probe(str(audio_path))
            
            # Extract duration from format section
            if 'format' not in probe_result:
                raise AudioAnalysisError(f"No format information found in audio file: {audio_path}")
            
            format_info = probe_result['format']
            if 'duration' not in format_info:
                raise AudioAnalysisError(f"No duration information found in audio file: {audio_path}")
            
            duration = float(format_info['duration'])
            
            # Validate duration is positive
            if duration <= 0:
                raise AudioAnalysisError(f"Invalid duration {duration} seconds in audio file: {audio_path}")
            
            logger.debug(f"Extracted duration: {duration:.3f} seconds from {audio_path}")
            return duration
            
        except ffmpeg.Error as e:
            error_msg = f"FFmpeg error while analyzing {audio_path}: {e}"
            logger.error(error_msg)
            raise AudioAnalysisError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to extract audio duration from {audio_path}: {e}"
            logger.error(error_msg)
            raise AudioAnalysisError(error_msg) from e
    
    def get_audio_metadata(self, audio_path: Path) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary containing audio metadata
            
        Raises:
            AudioAnalysisError: If metadata extraction fails
        """
        try:
            logger.debug(f"Extracting metadata from audio file: {audio_path}")
            
            # Validate file exists and format
            if not audio_path.exists():
                raise AudioAnalysisError(f"Audio file not found: {audio_path}")
            
            if audio_path.suffix.lower() not in self.supported_formats:
                raise AudioAnalysisError(
                    f"Unsupported audio format: {audio_path.suffix}. "
                    f"Supported formats: {', '.join(self.supported_formats)}"
                )
            
            # Use ffmpeg probe to get comprehensive information
            probe_result = ffmpeg.probe(str(audio_path))
            
            # Extract format information
            format_info = probe_result.get('format', {})
            
            # Extract stream information (audio stream)
            streams = probe_result.get('streams', [])
            audio_stream = None
            for stream in streams:
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise AudioAnalysisError(f"No audio stream found in file: {audio_path}")
            
            # Build metadata dictionary
            metadata = {
                'duration_seconds': float(format_info.get('duration', 0)),
                'file_size_bytes': int(format_info.get('size', 0)),
                'format_name': format_info.get('format_name', 'unknown'),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'codec_name': audio_stream.get('codec_name', 'unknown'),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'channel_layout': audio_stream.get('channel_layout', 'unknown'),
                'tags': format_info.get('tags', {})
            }
            
            # Validate essential metadata
            if metadata['duration_seconds'] <= 0:
                raise AudioAnalysisError(f"Invalid duration in audio file: {audio_path}")
            
            logger.debug(f"Extracted metadata from {audio_path}: duration={metadata['duration_seconds']:.3f}s, "
                        f"codec={metadata['codec_name']}, sample_rate={metadata['sample_rate']}")
            
            return metadata
            
        except ffmpeg.Error as e:
            error_msg = f"FFmpeg error while extracting metadata from {audio_path}: {e}"
            logger.error(error_msg)
            raise AudioAnalysisError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to extract audio metadata from {audio_path}: {e}"
            logger.error(error_msg)
            raise AudioAnalysisError(error_msg) from e
    
    def validate_audio_file(self, audio_path: Path) -> bool:
        """
        Validate that an audio file is supported and readable.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if file is valid
            
        Raises:
            AudioAnalysisError: If file is invalid
        """
        try:
            logger.debug(f"Validating audio file: {audio_path}")
            
            # Check file exists
            if not audio_path.exists():
                raise AudioAnalysisError(f"Audio file not found: {audio_path}")
            
            # Check file format
            if audio_path.suffix.lower() not in self.supported_formats:
                raise AudioAnalysisError(
                    f"Unsupported audio format: {audio_path.suffix}. "
                    f"Supported formats: {', '.join(self.supported_formats)}"
                )
            
            # Try to probe the file to ensure it's readable
            probe_result = ffmpeg.probe(str(audio_path))
            
            # Verify it has audio streams
            streams = probe_result.get('streams', [])
            has_audio = any(stream.get('codec_type') == 'audio' for stream in streams)
            
            if not has_audio:
                raise AudioAnalysisError(f"No audio stream found in file: {audio_path}")
            
            # Verify duration is available and positive
            format_info = probe_result.get('format', {})
            duration = float(format_info.get('duration', 0))
            
            if duration <= 0:
                raise AudioAnalysisError(f"Invalid or missing duration in audio file: {audio_path}")
            
            logger.debug(f"Audio file validation successful: {audio_path}")
            return True
            
        except ffmpeg.Error as e:
            error_msg = f"FFmpeg error while validating {audio_path}: {e}"
            logger.error(error_msg)
            raise AudioAnalysisError(error_msg) from e
        except Exception as e:
            error_msg = f"Audio file validation failed for {audio_path}: {e}"
            logger.error(error_msg)
            raise AudioAnalysisError(error_msg) from e
    
    def batch_analyze_audio_files(self, audio_paths: list[Path]) -> Dict[Path, Dict[str, Any]]:
        """
        Analyze multiple audio files and return their metadata.
        
        Args:
            audio_paths: List of audio file paths
            
        Returns:
            Dictionary mapping file paths to their metadata
            
        Raises:
            AudioAnalysisError: If any file analysis fails
        """
        results = {}
        
        for audio_path in audio_paths:
            try:
                metadata = self.get_audio_metadata(audio_path)
                results[audio_path] = metadata
            except AudioAnalysisError:
                # Re-raise to maintain error context
                raise
            except Exception as e:
                error_msg = f"Unexpected error analyzing {audio_path}: {e}"
                logger.error(error_msg)
                raise AudioAnalysisError(error_msg) from e
        
        logger.info(f"Successfully analyzed {len(results)} audio files")
        return results
    
    def get_total_duration(self, audio_paths: list[Path]) -> float:
        """
        Calculate total duration of multiple audio files.
        
        Args:
            audio_paths: List of audio file paths
            
        Returns:
            Total duration in seconds
            
        Raises:
            AudioAnalysisError: If any file analysis fails
        """
        total_duration = 0.0
        
        for audio_path in audio_paths:
            duration = self.get_audio_duration(audio_path)
            total_duration += duration
        
        logger.debug(f"Total duration of {len(audio_paths)} audio files: {total_duration:.3f} seconds")
        return total_duration