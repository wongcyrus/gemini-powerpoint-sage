"""File validation service for video synthesis."""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Set, Dict, Any, List, Tuple
from PIL import Image

from core.domain.video_synthesis import FileValidationError

logger = logging.getLogger(__name__)


class FileValidator:
    """Service for validating image and audio files for video synthesis."""
    
    def __init__(self):
        """Initialize file validator."""
        self.supported_image_formats = {'.png', '.jpg', '.jpeg'}
        self.supported_audio_formats = {'.mp3'}
    
    def validate_image_file(self, image_path: Path) -> Dict[str, Any]:
        """
        Validate image file and return metadata.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary containing image metadata
            
        Raises:
            FileValidationError: If file is invalid
        """
        try:
            logger.debug(f"Validating image file: {image_path}")
            
            # Check file exists
            if not image_path.exists():
                raise FileValidationError(f"Image file not found: {image_path}")
            
            # Check file extension
            file_ext = image_path.suffix.lower()
            if file_ext not in self.supported_image_formats:
                raise FileValidationError(
                    f"Unsupported image format: {file_ext}. "
                    f"Supported formats: {', '.join(self.supported_image_formats)}"
                )
            
            # Try to open and validate the image using PIL
            try:
                with Image.open(image_path) as img:
                    # Verify image can be loaded
                    img.verify()
                
                # Reopen to get metadata (verify() closes the image)
                with Image.open(image_path) as img:
                    width, height = img.size
                    mode = img.mode
                    format_name = img.format
                    
                    # Validate image dimensions
                    if width <= 0 or height <= 0:
                        raise FileValidationError(f"Invalid image dimensions: {width}x{height}")
                    
                    # Get file size
                    file_size = image_path.stat().st_size
                    
                    metadata = {
                        'width': width,
                        'height': height,
                        'mode': mode,
                        'format': format_name,
                        'file_size_bytes': file_size,
                        'aspect_ratio': width / height,
                        'file_extension': file_ext
                    }
                    
                    logger.debug(f"Image validation successful: {image_path} ({width}x{height}, {format_name})")
                    return metadata
                    
            except Exception as e:
                raise FileValidationError(f"Invalid or corrupted image file {image_path}: {e}")
            
        except FileValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error validating image file {image_path}: {e}"
            logger.error(error_msg)
            raise FileValidationError(error_msg) from e
    
    def validate_audio_file(self, audio_path: Path) -> Dict[str, Any]:
        """
        Validate audio file and return metadata using direct FFmpeg commands.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary containing audio metadata
            
        Raises:
            FileValidationError: If file is invalid
        """
        try:
            logger.debug(f"Validating audio file: {audio_path}")
            
            # Check file exists
            if not audio_path.exists():
                raise FileValidationError(f"Audio file not found: {audio_path}")
            
            # Check file extension
            file_ext = audio_path.suffix.lower()
            if file_ext not in self.supported_audio_formats:
                raise FileValidationError(
                    f"Unsupported audio format: {file_ext}. "
                    f"Supported formats: {', '.join(self.supported_audio_formats)}"
                )
            
            # Use direct FFmpeg probe command to validate and get metadata
            try:
                cmd = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    str(audio_path)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout for probe
                )
                
                if result.returncode != 0:
                    raise FileValidationError(f"FFprobe failed for audio file {audio_path}: {result.stderr}")
                
                # Parse JSON output
                probe_result = json.loads(result.stdout)
                
                # Verify it has audio streams
                streams = probe_result.get('streams', [])
                audio_stream = None
                for stream in streams:
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                if not audio_stream:
                    raise FileValidationError(f"No audio stream found in file: {audio_path}")
                
                # Extract format information
                format_info = probe_result.get('format', {})
                
                # Validate duration
                duration = float(format_info.get('duration', 0))
                if duration <= 0:
                    raise FileValidationError(f"Invalid or missing duration in audio file: {audio_path}")
                
                # Build metadata
                metadata = {
                    'duration_seconds': duration,
                    'file_size_bytes': int(format_info.get('size', 0)),
                    'format_name': format_info.get('format_name', 'unknown'),
                    'bit_rate': int(format_info.get('bit_rate', 0)),
                    'codec_name': audio_stream.get('codec_name', 'unknown'),
                    'sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'channels': int(audio_stream.get('channels', 0)),
                    'file_extension': file_ext
                }
                
                logger.debug(f"Audio validation successful: {audio_path} ({duration:.3f}s, {metadata['codec_name']})")
                return metadata
                
            except subprocess.TimeoutExpired:
                raise FileValidationError(f"Audio validation timed out for file: {audio_path}")
            except FileNotFoundError:
                raise FileValidationError("FFprobe not found. Please install FFmpeg and ensure it's in your PATH.")
            except json.JSONDecodeError as e:
                raise FileValidationError(f"Failed to parse FFprobe output for {audio_path}: {e}")
            except Exception as e:
                raise FileValidationError(f"FFprobe error for audio file {audio_path}: {e}")
            
        except FileValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error validating audio file {audio_path}: {e}"
            logger.error(error_msg)
            raise FileValidationError(error_msg) from e
    
    def validate_slide_audio_pairs(self, slide_images: List[Path], audio_files: List[Path]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Validate pairs of slide images and audio files.
        
        Args:
            slide_images: List of slide image paths
            audio_files: List of audio file paths
            
        Returns:
            List of tuples containing (image_metadata, audio_metadata) for each pair
            
        Raises:
            FileValidationError: If validation fails for any file or pairing
        """
        try:
            logger.info(f"Validating {len(slide_images)} slide-audio pairs")
            
            # Validate counts match
            if len(slide_images) != len(audio_files):
                raise FileValidationError(
                    f"Number of slide images ({len(slide_images)}) must match "
                    f"number of audio files ({len(audio_files)})"
                )
            
            if not slide_images:
                raise FileValidationError("At least one slide-audio pair is required")
            
            validated_pairs = []
            
            for i, (image_path, audio_path) in enumerate(zip(slide_images, audio_files)):
                try:
                    logger.debug(f"Validating pair {i+1}: {image_path.name} + {audio_path.name}")
                    
                    # Validate image
                    image_metadata = self.validate_image_file(image_path)
                    
                    # Validate audio
                    audio_metadata = self.validate_audio_file(audio_path)
                    
                    validated_pairs.append((image_metadata, audio_metadata))
                    
                except FileValidationError as e:
                    raise FileValidationError(f"Validation failed for pair {i+1} ({image_path.name}, {audio_path.name}): {e}")
            
            logger.info(f"Successfully validated {len(validated_pairs)} slide-audio pairs")
            return validated_pairs
            
        except FileValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error validating slide-audio pairs: {e}"
            logger.error(error_msg)
            raise FileValidationError(error_msg) from e
    
    def get_unsupported_files(self, file_paths: List[Path]) -> Dict[str, List[Path]]:
        """
        Identify unsupported files from a list of paths.
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            Dictionary with 'unsupported_images', 'unsupported_audio', and 'unknown' lists
        """
        result = {
            'unsupported_images': [],
            'unsupported_audio': [],
            'unknown': []
        }
        
        for file_path in file_paths:
            if not file_path.exists():
                result['unknown'].append(file_path)
                continue
            
            file_ext = file_path.suffix.lower()
            
            # Check if it's an image format (supported or unsupported)
            if file_ext in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}:
                if file_ext not in self.supported_image_formats:
                    result['unsupported_images'].append(file_path)
            # Check if it's an audio format (supported or unsupported)
            elif file_ext in {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}:
                if file_ext not in self.supported_audio_formats:
                    result['unsupported_audio'].append(file_path)
            else:
                result['unknown'].append(file_path)
        
        return result
    
    def generate_format_error_message(self, unsupported_files: Dict[str, List[Path]]) -> str:
        """
        Generate a detailed error message for unsupported file formats.
        
        Args:
            unsupported_files: Dictionary from get_unsupported_files()
            
        Returns:
            Formatted error message
        """
        messages = []
        
        if unsupported_files['unsupported_images']:
            image_files = [f.name for f in unsupported_files['unsupported_images']]
            messages.append(
                f"Unsupported image formats: {', '.join(image_files)}. "
                f"Supported image formats: {', '.join(self.supported_image_formats)}"
            )
        
        if unsupported_files['unsupported_audio']:
            audio_files = [f.name for f in unsupported_files['unsupported_audio']]
            messages.append(
                f"Unsupported audio formats: {', '.join(audio_files)}. "
                f"Supported audio formats: {', '.join(self.supported_audio_formats)}"
            )
        
        if unsupported_files['unknown']:
            unknown_files = [f.name for f in unsupported_files['unknown']]
            messages.append(f"Unknown or missing files: {', '.join(unknown_files)}")
        
        return "; ".join(messages)
    
    def validate_output_path(self, output_path: Path) -> None:
        """
        Validate output path for video file.
        
        Args:
            output_path: Desired output file path
            
        Raises:
            FileValidationError: If output path is invalid
        """
        try:
            # Check if parent directory exists or can be created
            parent_dir = output_path.parent
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise FileValidationError(f"Cannot create output directory {parent_dir}: {e}")
            
            # Check if parent directory is writable
            if not os.access(parent_dir, os.W_OK):
                raise FileValidationError(f"Output directory is not writable: {parent_dir}")
            
            # Validate file extension
            file_ext = output_path.suffix.lower()
            valid_video_formats = {'.mp4', '.avi', '.mkv', '.webm'}
            if file_ext not in valid_video_formats:
                raise FileValidationError(
                    f"Unsupported output video format: {file_ext}. "
                    f"Supported formats: {', '.join(valid_video_formats)}"
                )
            
            logger.debug(f"Output path validation successful: {output_path}")
            
        except FileValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error validating output path {output_path}: {e}"
            logger.error(error_msg)
            raise FileValidationError(error_msg) from e