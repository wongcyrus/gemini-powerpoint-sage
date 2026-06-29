"""Video synthesis domain models."""

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class VideoConfig:
    """Configuration for video synthesis."""
    
    resolution: Tuple[int, int] = (1920, 1080)  # Output resolution
    fps: int = 30                               # Frames per second
    video_codec: str = "libx264"               # Video codec
    audio_codec: str = "aac"                   # Audio codec
    video_bitrate: str = "1M"                  # Video bitrate
    audio_bitrate: str = "96k"                 # Audio bitrate
    output_format: str = "mp4"                 # Output format
    fade_duration: float = 0.5                 # Transition fade duration
    
    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.resolution[0] <= 0 or self.resolution[1] <= 0:
            raise ValueError("Resolution must have positive width and height")
        
        if self.fps <= 0:
            raise ValueError("FPS must be positive")
        
        if self.fade_duration < 0:
            raise ValueError("Fade duration cannot be negative")
        
        # Validate video codec
        valid_video_codecs = ["libx264", "libx265", "libvpx", "libvpx-vp9"]
        if self.video_codec not in valid_video_codecs:
            raise ValueError(f"Video codec must be one of: {valid_video_codecs}")
        
        # Validate audio codec
        valid_audio_codecs = ["aac", "mp3", "libvorbis", "libopus"]
        if self.audio_codec not in valid_audio_codecs:
            raise ValueError(f"Audio codec must be one of: {valid_audio_codecs}")
        
        # Validate output format
        valid_formats = ["mp4", "avi", "mkv", "webm"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Output format must be one of: {valid_formats}")


@dataclass
class SlideVideoSegment:
    """Represents a single slide-audio pair for video generation."""
    
    slide_index: int
    image_path: Path
    audio_path: Path
    duration_seconds: float  # Extracted from audio file duration
    temp_video_path: Optional[Path] = None
    
    def __post_init__(self):
        """Validate segment after initialization."""
        if not isinstance(self.image_path, Path):
            self.image_path = Path(self.image_path)
        
        if not isinstance(self.audio_path, Path):
            self.audio_path = Path(self.audio_path)
        
        if not self.image_path.exists():
            raise ValueError(f"Image file not found: {self.image_path}")
        
        if not self.audio_path.exists():
            raise ValueError(f"Audio file not found: {self.audio_path}")
        
        if self.duration_seconds <= 0:
            raise ValueError("Duration must be positive")
    
    @classmethod
    def from_files(cls, slide_index: int, image_path: Path, audio_path: Path) -> 'SlideVideoSegment':
        """Create segment with duration extracted from audio file."""
        duration = cls._get_audio_duration(audio_path)
        return cls(slide_index, image_path, audio_path, duration)
    
    @staticmethod
    def _get_audio_duration(audio_path: Path) -> float:
        """Extract duration from audio file using direct FFmpeg probe command."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                str(audio_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout for probe
            )
            
            if result.returncode != 0:
                raise ValueError(f"FFprobe failed for audio file {audio_path}: {result.stderr}")
            
            # Parse JSON output
            probe_result = json.loads(result.stdout)
            format_info = probe_result.get('format', {})
            duration = float(format_info.get('duration', 0))
            
            if duration <= 0:
                raise ValueError(f"Invalid or missing duration in audio file: {audio_path}")
            
            return duration
            
        except subprocess.TimeoutExpired:
            raise ValueError(f"Audio duration extraction timed out for file: {audio_path}")
        except FileNotFoundError:
            raise ValueError("FFprobe not found. Please install FFmpeg and ensure it's in your PATH.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse FFprobe output for {audio_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to extract audio duration from {audio_path}: {e}")
    
    def validate_formats(self) -> None:
        """Validate that image and audio files are in supported formats."""
        # Validate image format
        image_ext = self.image_path.suffix.lower()
        if image_ext not in ['.png', '.jpg', '.jpeg']:
            raise ValueError(f"Unsupported image format: {image_ext}. Supported formats: PNG, JPG, JPEG")
        
        # Validate audio format
        audio_ext = self.audio_path.suffix.lower()
        if audio_ext not in ['.mp3']:
            raise ValueError(f"Unsupported audio format: {audio_ext}. Supported formats: MP3")


@dataclass
class VideoSynthesisRequest:
    """Request for video synthesis operation."""
    
    slide_images: List[Path]  # Ordered list of slide image paths
    audio_files: List[Path]   # Corresponding audio file paths
    output_path: Path         # Desired output video path
    config: VideoConfig       # Video generation configuration
    presentation_id: str      # Presentation identifier for tracking
    inserted_video_paths_before: Dict[int, List[Path]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate request after initialization."""
        if not isinstance(self.output_path, Path):
            self.output_path = Path(self.output_path)
        
        # Convert string paths to Path objects
        self.slide_images = [Path(p) if not isinstance(p, Path) else p for p in self.slide_images]
        self.audio_files = [Path(p) if not isinstance(p, Path) else p for p in self.audio_files]
        normalized_inserts: Dict[int, List[Path]] = {}
        for slide_idx, paths in self.inserted_video_paths_before.items():
            normalized_inserts[int(slide_idx)] = [
                Path(p) if not isinstance(p, Path) else p for p in paths
            ]
        self.inserted_video_paths_before = normalized_inserts

        self.validate()
    
    def validate(self) -> None:
        """Validate the synthesis request."""
        if not self.slide_images:
            raise ValueError("At least one slide image is required")
        
        if not self.audio_files:
            raise ValueError("At least one audio file is required")
        
        if len(self.slide_images) != len(self.audio_files):
            raise ValueError(f"Number of slide images ({len(self.slide_images)}) must match number of audio files ({len(self.audio_files)})")
        
        if not self.presentation_id:
            raise ValueError("Presentation ID is required")
        
        # Validate all files exist
        for i, image_path in enumerate(self.slide_images):
            if not image_path.exists():
                raise ValueError(f"Slide image {i+1} not found: {image_path}")
        
        for i, audio_path in enumerate(self.audio_files):
            if not audio_path.exists():
                raise ValueError(f"Audio file {i+1} not found: {audio_path}")

        for slide_idx, video_paths in self.inserted_video_paths_before.items():
            if slide_idx <= 0:
                raise ValueError("Inserted video slide indices must be positive")
            for i, video_path in enumerate(video_paths):
                if not video_path.exists():
                    raise ValueError(
                        f"Inserted video {i+1} for slide {slide_idx} not found: {video_path}"
                    )

        # Validate configuration
        self.config.validate()
    
    def create_segments(self) -> List[SlideVideoSegment]:
        """Create video segments from slide images and audio files."""
        segments = []
        for i, (image_path, audio_path) in enumerate(zip(self.slide_images, self.audio_files)):
            # Extract slide number from filenames for proper indexing
            slide_number = self._extract_slide_number_from_files(image_path, audio_path)
            segment = SlideVideoSegment.from_files(slide_number, image_path, audio_path)
            segment.validate_formats()
            segments.append(segment)
        return segments
    
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


@dataclass
class VideoSynthesisResult:
    """Result of video synthesis operation."""
    
    success: bool
    output_path: Optional[Path]
    duration_seconds: float
    file_size_bytes: int
    processing_time_seconds: float
    error_message: Optional[str] = None
    slides_processed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate result after initialization."""
        if self.success and not self.output_path:
            raise ValueError("Successful result must have output path")
        
        if not self.success and not self.error_message:
            raise ValueError("Failed result must have error message")
        
        if self.duration_seconds < 0:
            raise ValueError("Duration cannot be negative")
        
        if self.file_size_bytes < 0:
            raise ValueError("File size cannot be negative")
        
        if self.processing_time_seconds < 0:
            raise ValueError("Processing time cannot be negative")
        
        if self.slides_processed < 0:
            raise ValueError("Slides processed cannot be negative")
    
    @classmethod
    def success_result(
        cls,
        output_path: Path,
        duration_seconds: float,
        file_size_bytes: int,
        processing_time_seconds: float,
        slides_processed: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'VideoSynthesisResult':
        """Create a successful result."""
        return cls(
            success=True,
            output_path=output_path,
            duration_seconds=duration_seconds,
            file_size_bytes=file_size_bytes,
            processing_time_seconds=processing_time_seconds,
            slides_processed=slides_processed,
            metadata=metadata or {}
        )
    
    @classmethod
    def failure_result(
        cls,
        error_message: str,
        processing_time_seconds: float = 0.0,
        slides_processed: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'VideoSynthesisResult':
        """Create a failed result."""
        return cls(
            success=False,
            output_path=None,
            duration_seconds=0.0,
            file_size_bytes=0,
            processing_time_seconds=processing_time_seconds,
            error_message=error_message,
            slides_processed=slides_processed,
            metadata=metadata or {}
        )
    
    def get_file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)
    
    def get_processing_rate(self) -> float:
        """Get processing rate in slides per second."""
        if self.processing_time_seconds <= 0:
            return 0.0
        return self.slides_processed / self.processing_time_seconds


class VideoSynthesisError(Exception):
    """Base exception for video synthesis errors."""
    pass


class VideoConfigurationError(VideoSynthesisError):
    """Exception for video configuration errors."""
    pass


class VideoProcessingError(VideoSynthesisError):
    """Exception for video processing errors."""
    pass


class AudioAnalysisError(VideoSynthesisError):
    """Exception for audio analysis errors."""
    pass


class FileValidationError(VideoSynthesisError):
    """Exception for file validation errors."""
    pass