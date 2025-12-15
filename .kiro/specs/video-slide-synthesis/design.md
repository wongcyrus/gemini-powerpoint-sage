# Video Slide Synthesis Design Document

## Overview

The Video Slide Synthesis feature enables automatic generation of presentation videos by combining slide images with corresponding MP3 audio files. The system leverages the python-ffmpeg library to create synchronized video content where each slide is displayed for the duration of its corresponding audio narration. This feature integrates with the existing presentation processing pipeline and follows established patterns for file management, configuration, and error handling.

## Architecture

The video synthesis system follows a service-oriented architecture that integrates with the existing codebase structure:

```
VideoSynthesisService
├── FFmpegVideoProcessor (core video processing)
├── VideoConfigManager (configuration management)
├── VideoFileManager (file operations and cleanup)
└── VideoProgressTracker (progress reporting)
```

The system integrates with existing services:
- `FileService` for file validation and management
- `Config` for configuration and output directory management
- Existing logging and error handling infrastructure

## Components and Interfaces

### VideoSynthesisService
Main orchestrator service that coordinates video generation:
- Manages the overall video synthesis workflow
- Coordinates between file management, processing, and progress tracking
- Handles error recovery and cleanup operations
- Provides public API for video generation

### FFmpegVideoProcessor
Core video processing engine using python-ffmpeg:
- Handles ffmpeg command construction and execution
- Manages video encoding parameters and quality settings
- Processes individual slide-audio pairs into video segments
- **Determines slide display duration from corresponding audio file duration**
- Combines segments into final presentation video with seamless transitions

### VideoConfigManager
Configuration management for video synthesis:
- Manages video quality settings (resolution, codec, bitrate)
- Handles output format configuration
- Provides validation for configuration parameters
- Integrates with existing Config class patterns

### VideoFileManager
File operations and temporary file management:
- Creates and manages temporary working directories
- Handles file validation for images and audio
- Manages cleanup of temporary files
- Provides file path resolution and organization

### VideoProgressTracker
Progress reporting and status management:
- Tracks processing progress across multiple slides
- Provides real-time status updates
- Handles error reporting and recovery status
- Integrates with existing logging infrastructure

## Slide Timing Mechanism

The system determines how long each slide is displayed based on the duration of its corresponding audio file:

### Audio Duration Extraction
1. **Audio File Analysis**: For each MP3 file, the system uses ffmpeg-python's probe functionality to extract the exact duration in seconds
2. **Precision**: Duration is captured with millisecond precision to ensure accurate synchronization
3. **Validation**: Audio files are validated to ensure they contain valid audio streams before duration extraction

### Slide-Audio Pairing
1. **File Matching**: Slides and audio files are paired based on:
   - Explicit ordering provided in the VideoSynthesisRequest
   - File naming conventions (e.g., slide_01.png with audio_01.mp3)
   - Sequential processing order
2. **Validation**: The system validates that each slide has a corresponding audio file
3. **Error Handling**: Missing audio files or mismatched pairs result in clear error messages

### Video Segment Creation
1. **Static Display**: Each slide image is displayed as a static frame for the entire duration of its audio
2. **Audio Synchronization**: The audio track plays simultaneously with the slide display
3. **Seamless Transitions**: Optional fade transitions between slides (configurable duration)

### Example Workflow
```
Slide 1 (slide_01.png) + Audio 1 (audio_01.mp3, 45.2 seconds) → Video Segment 1 (45.2 seconds)
Slide 2 (slide_02.png) + Audio 2 (audio_02.mp3, 32.8 seconds) → Video Segment 2 (32.8 seconds)
Slide 3 (slide_03.png) + Audio 3 (audio_03.mp3, 51.1 seconds) → Video Segment 3 (51.1 seconds)
Final Video: 129.1 seconds total (45.2 + 32.8 + 51.1)
```

## Data Models

### VideoSynthesisRequest
```python
@dataclass
class VideoSynthesisRequest:
    slide_images: List[Path]  # Ordered list of slide image paths
    audio_files: List[Path]   # Corresponding audio file paths
    output_path: Path         # Desired output video path
    config: VideoConfig       # Video generation configuration
    presentation_id: str      # Presentation identifier for tracking
```

### VideoConfig
```python
@dataclass
class VideoConfig:
    resolution: Tuple[int, int] = (1920, 1080)  # Output resolution
    fps: int = 30                               # Frames per second
    video_codec: str = "libx264"               # Video codec
    audio_codec: str = "aac"                   # Audio codec
    video_bitrate: str = "2M"                  # Video bitrate
    audio_bitrate: str = "128k"                # Audio bitrate
    output_format: str = "mp4"                 # Output format
    fade_duration: float = 0.5                 # Transition fade duration
```

### VideoSynthesisResult
```python
@dataclass
class VideoSynthesisResult:
    success: bool
    output_path: Optional[Path]
    duration_seconds: float
    file_size_bytes: int
    processing_time_seconds: float
    error_message: Optional[str] = None
    slides_processed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### SlideVideoSegment
```python
@dataclass
class SlideVideoSegment:
    slide_index: int
    image_path: Path
    audio_path: Path
    duration_seconds: float  # Extracted from audio file duration
    temp_video_path: Optional[Path] = None
    
    @classmethod
    def from_files(cls, slide_index: int, image_path: Path, audio_path: Path) -> 'SlideVideoSegment':
        """Create segment with duration extracted from audio file."""
        duration = cls._get_audio_duration(audio_path)
        return cls(slide_index, image_path, audio_path, duration)
    
    @staticmethod
    def _get_audio_duration(audio_path: Path) -> float:
        """Extract duration from audio file using ffmpeg probe."""
        # Implementation will use ffmpeg-python to probe audio duration
        pass
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

After analyzing the acceptance criteria, I identified several properties that can be consolidated to eliminate redundancy:

**Property Reflection:**
- Properties 2.1, 2.2, and 2.3 (format support) can be combined into a single comprehensive format support property
- Properties 3.1, 3.2, 3.3, 3.4, and 3.5 (configuration) can be consolidated into one configuration application property
- Properties 4.1, 4.2, 4.4 (progress reporting) can be combined into a comprehensive progress reporting property
- Properties 5.2 and 5.3 (cleanup) can be unified into a single cleanup property covering both success and failure cases

### Property 1: Audio-Visual Synchronization
*For any* slide with corresponding audio file, the generated video segment duration should exactly match the audio file duration
**Validates: Requirements 1.3**

### Property 2: Slide Sequence Preservation
*For any* ordered list of slides, the output video should maintain the exact same sequence order
**Validates: Requirements 1.2**

### Property 3: Single Output Generation
*For any* set of slides and audio files, the video synthesis should produce exactly one output video file containing all processed content
**Validates: Requirements 1.1, 1.5**

### Property 4: Format Support Consistency
*For any* supported file format (PNG, JPG images and MP3 audio), the video synthesis should process them successfully without format conversion
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 5: Unsupported Format Rejection
*For any* unsupported file format, the video synthesis should reject the input with clear error messages indicating supported formats
**Validates: Requirements 2.4**

### Property 6: Resolution Standardization
*For any* set of images with different resolutions, the output video should have consistent resolution as specified in configuration
**Validates: Requirements 2.5**

### Property 7: Configuration Application
*For any* valid video configuration parameters (resolution, codec, format, quality), all specified settings should be reflected in the final output video properties
**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 8: Progress Reporting
*For any* video synthesis operation, the system should provide progress indicators, slide-specific status updates, and completion confirmation with file details
**Validates: Requirements 4.1, 4.2, 4.4**

### Property 9: Error Reporting
*For any* processing error, the system should provide detailed error messages with sufficient context for diagnosis
**Validates: Requirements 4.3**

### Property 10: Temporary File Cleanup
*For any* video synthesis operation (successful or failed), all temporary files and directories should be removed after processing completion
**Validates: Requirements 5.1, 5.2, 5.3**

### Property 11: Concurrent Operation Isolation
*For any* two concurrent video synthesis operations, temporary files and processing should not interfere with each other
**Validates: Requirements 5.4**

### Property 12: Cancellation Handling
*For any* cancelled video synthesis operation, the system should clean up temporary files and report cancellation status
**Validates: Requirements 4.5**

## Error Handling

The video synthesis system implements comprehensive error handling:

### Input Validation Errors
- Missing or invalid image files
- Missing or invalid audio files
- Unsupported file formats
- Mismatched slide-audio pairs

### Processing Errors
- FFmpeg execution failures
- Insufficient disk space
- Memory allocation issues
- Codec compatibility problems

### Configuration Errors
- Invalid video parameters
- Unsupported output formats
- Invalid resolution settings

### Recovery Strategies
- Automatic cleanup of temporary files on failure
- Detailed error logging with context
- Graceful degradation for non-critical errors
- Retry mechanisms for transient failures

## Testing Strategy

### Unit Testing
The system will include comprehensive unit tests covering:
- Individual component functionality
- Configuration validation
- File operation handling
- Error condition responses

### Property-Based Testing
Property-based tests will verify correctness properties using the Hypothesis library:
- Generate random slide sets and verify synchronization
- Test various configuration combinations
- Validate cleanup behavior across different failure scenarios
- Verify concurrent operation isolation

**Property-Based Testing Configuration:**
- Library: Hypothesis (Python property-based testing framework)
- Minimum iterations: 100 per property test
- Each property test will be tagged with format: `**Feature: video-slide-synthesis, Property {number}: {property_text}**`
- Property tests will focus on core correctness guarantees rather than implementation details

### Integration Testing
- End-to-end video generation workflows
- Integration with existing presentation processing pipeline
- File system interaction testing
- Performance testing with various slide counts and sizes

The testing approach ensures both specific examples work correctly (unit tests) and universal properties hold across all inputs (property tests), providing comprehensive coverage for reliable video synthesis functionality.