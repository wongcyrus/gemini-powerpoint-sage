# Video Synthesis Setup Guide

## Overview

The video synthesis feature combines slide images with audio files to create presentation videos. Key features include:

- **Same Directory Storage**: MP3 audio files and slide images are stored in the same directory for simplified workflow
- **Intelligent Caching**: Automatic caching of video segments for 2-5x faster reruns
- **Flexible Configuration**: Multiple video quality presets and custom configurations
- **CLI Integration**: Easy-to-use command-line interface with cache management

## ⚠️ Critical Prerequisites

**Video synthesis requires ALL slides to be successful:**

1. **Complete Dependency Chain**: Speaker Notes → Images → Audio → Video Synthesis
2. **No Failed Slides**: Any slide with `"status": "error"` will break video synthesis
3. **Exact File Pairing**: Must have matching slide images and audio files (1:1 ratio)
4. **Sequential Naming**: Missing any slide creates misaligned pairing

**Before video synthesis, verify all slides succeeded:**
```bash
# Check for any failed slides
grep -r "status.*error" notes/*/generate/*.json

# If failures found, fix them first:
python main.py --styles --retry-errors

# Verify readiness
python main.py --video-cache-stats  # Shows file counts per presentation
```

**Common failure scenario:**
- Slide 16 speaker notes fail → No slide_16.png, no slide_16.mp3
- Video synthesis gets 45 images + 45 audio files but misaligned
- Result: slide_17.png paired with slide_16.mp3 (wrong content!)

See [Error Handling Guide](docs/ERROR_HANDLING.md) for detailed troubleshooting.

## Key Changes Made

### 1. Directory Structure Update

**Before:**
- Slide images: `generate/style/presentation_en_visuals/`
- Audio files: `generate/style/presentation_en_speech/`

**After:**
- Slide images: `generate/style/presentation_en_visuals/`
- Audio files: `generate/style/presentation_en_visuals/` (same directory!)

### 2. Configuration Changes

Updated `config/config.py`:
```python
@property
def speech_dir(self) -> str:
    """Get the directory for storing speech outputs (same as visuals directory)."""
    # Use the same directory as visuals to keep MP3 and visual files together
    return self.visuals_dir
```

### 3. CLI Improvements

Updated CLI arguments:
- `--audio-dir` is now optional
- If not specified, `--slides-dir` is used for both slides and audio
- Added helpful messages showing which directories are being used

### 4. Integration Enhancements

Added new convenience method:
```python
def create_video_from_visuals_directory(self, presentation, output_filename=None):
    """Create video using the visuals directory for both slides and audio."""
```

### 5. Caching System

Added intelligent caching for video segments:
- **Automatic caching**: Video segments cached based on content hash + configuration
- **Persistent storage**: Cache survives between application runs
- **Smart cache keys**: SHA256 hash ensures cache hits only for identical inputs
- **Cache management**: CLI commands for viewing stats and clearing cache

## Usage Examples

### Basic Workflow

1. **Generate presentation with visuals and TTS:**
   ```bash
   ./run.sh --style-config hkcomic
   ```

2. **Synthesize video from the generated files:**
   ```bash
   python main.py --synthesize-video \
     --slides-dir generate/hkcomic/presentation_en_visuals \
     --video-output generate/hkcomic/presentation_video.mp4
   ```

### CLI Options

**Single directory (recommended):**
```bash
python main.py --synthesize-video \
  --slides-dir path/to/visuals_directory \
  --video-output output/video.mp4
```

**Separate directories (if needed):**
```bash
python main.py --synthesize-video \
  --slides-dir path/to/slides \
  --audio-dir path/to/audio \
  --video-output output/video.mp4
```

Default encoding now uses `video_bitrate: "1M"` and `audio_bitrate: "96k"` to keep combined files smaller.

**With custom configuration:**
```bash
python main.py --synthesize-video \
  --slides-dir path/to/visuals_directory \
  --video-output output/video_hd.mp4 \
  --video-config '{"resolution": [1280, 720], "video_bitrate": "1.5M"}'
```

### Cache Management

**View cache statistics:**
```bash
python main.py --video-cache-stats
```

**Clear entire cache:**
```bash
python main.py --video-clear-cache 0
```

**Clear cache files older than 7 days:**
```bash
python main.py --video-clear-cache 7
```

### Programmatic Usage

```python
from services.video_synthesis.integration import VideoSynthesisIntegration
from config.config import Config

# Create config and integration
config = Config(pptx_path="presentation.pptx", pdf_path="presentation.pdf")
integration = VideoSynthesisIntegration(config)

# Create video from visuals directory (easiest method)
video_path = integration.create_video_from_visuals_directory(presentation)

# Or specify directories explicitly
video_path = integration.create_video_from_presentation(
    presentation=presentation,
    slide_images_dir=Path("visuals/"),
    audio_files_dir=Path("visuals/"),  # Same directory
    output_filename="my_video.mp4"
)
```

## File Patterns

After running `./run.sh --style-config hkcomic`, the visuals directory will contain:

```
generate/hkcomic/presentation_en_visuals/
├── slide_1_reimagined.png    # Slide image
├── slide_1_<hash>.mp3        # Audio for slide 1
├── slide_2_reimagined.png    # Slide image
├── slide_2_<hash>.mp3        # Audio for slide 2
├── slide_3_reimagined.png    # Slide image
├── slide_3_<hash>.mp3        # Audio for slide 3
└── ...
```

## Video Configuration Options

### Preset Configurations

- **Default (Full HD):** 1920x1080, 30fps, H.264, 2M bitrate
- **HD:** 1280x720, 30fps, H.264, 1.5M bitrate  
- **4K:** 3840x2160, 30fps, H.264, 8M bitrate
- **Web Optimized:** 1280x720, 30fps, H.264, 1M bitrate

### Custom Configuration

```json
{
  "resolution": [1920, 1080],
  "fps": 30,
  "video_codec": "libx264",
  "audio_codec": "aac",
  "video_bitrate": "2M",
  "audio_bitrate": "128k",
  "output_format": "mp4",
  "fade_duration": 0.5
}
```

## Dependencies

To use video synthesis, install the required dependency:
```bash
pip install ffmpeg-python
```

Note: The system also requires FFmpeg to be installed on the system.

## Testing

**Run the workflow demonstration:**
```bash
python examples/video_synthesis_workflow.py
```

**Test caching performance:**
```bash
python examples/video_synthesis_cache_demo.py
```

**Run basic video synthesis test:**
```bash
python test_video_synthesis.py
```

These scripts will demonstrate the complete workflow, test caching performance, and validate the configuration.

## Caching System Details

### How Caching Works

1. **Cache Key Generation**: Each video segment gets a unique cache key based on:
   - Image file content (SHA256 hash)
   - Audio file content (SHA256 hash)  
   - Video configuration settings (resolution, codecs, bitrates, etc.)

2. **Cache Storage**: Cached segments stored in `./cache/video_synthesis/`
   ```
   cache/video_synthesis/
   ├── segment_abc123def456.mp4  # Cached video segments
   ├── segment_789xyz012345.mp4
   ├── cache_metadata.json       # Cache metadata
   └── ...
   ```

3. **Cache Lookup**: Before creating each segment:
   - Generate cache key for current inputs
   - Check if cached segment exists
   - If found, copy to temp directory (fast)
   - If not found, create segment and cache it

4. **Performance Benefits**:
   - **First run**: Normal processing time, segments cached
   - **Subsequent runs**: 2-5x faster, only concatenation needed
   - **Partial changes**: Only changed segments re-processed

### Cache Management

- **Automatic cleanup**: Temporary files cleaned up, cache persists
- **Manual management**: CLI commands for viewing stats and clearing cache
- **Storage efficient**: Only stores unique segments, shared across presentations
- **Safe caching**: Cache keys ensure no false positives

## File Sorting Fix

### Natural Sorting Implementation

✅ **Fixed**: The system now uses **natural sorting** to pair slides and audio files correctly:

1. **Natural Sorting**: Files are sorted by numeric value, not alphabetically
   - `slide_1.png`, `slide_2.png`, ..., `slide_10.png`, `slide_11.png` ✓
   - Not: `slide_1.png`, `slide_10.png`, `slide_11.png`, ..., `slide_2.png` ❌

2. **Automatic Verification**: The system shows file pairing preview and verifies slide numbers match

3. **Pairing Process**:
   - Both slide images and audio files are sorted using natural sorting
   - Files are paired by index position after sorting
   - System extracts slide numbers from filenames to verify correct pairing

**File Naming Examples** (all work correctly now):
```
✅ Works perfectly:
slide_1_reimagined.png → slide_1_hash.mp3
slide_2_reimagined.png → slide_2_hash.mp3
slide_10_reimagined.png → slide_10_hash.mp3

✅ Also works (zero-padded):
slide_01_reimagined.png → slide_01_hash.mp3
slide_02_reimagined.png → slide_02_hash.mp3
slide_10_reimagined.png → slide_10_hash.mp3
```

**Pairing Verification**: The system automatically shows a preview like:
```
File pairing preview (first 5):
  1: slide_1_reimagined.png + slide_1_abc123.mp3 ✓ (slide 1 + 1)
  2: slide_2_reimagined.png + slide_2_def456.mp3 ✓ (slide 2 + 2)
  3: slide_3_reimagined.png + slide_3_ghi789.mp3 ✓ (slide 3 + 3)
  ... and 47 more pairs
✓ File pairing verification passed
```

## Benefits Summary

### Same Directory Structure
1. **Simplified workflow** - Only need to specify one directory
2. **Easier file management** - All related files in one place
3. **Reduced errors** - No need to keep track of multiple directories
4. **Better organization** - Logical grouping of presentation assets
5. **Seamless integration** - Works naturally with existing processing pipeline

### Intelligent Caching
1. **Significant speedup** - 2-5x faster for reruns with same content
2. **Development friendly** - Quick iterations during testing and refinement
3. **Resource efficient** - Reuses computation, saves processing time
4. **Persistent storage** - Cache survives application restarts
5. **Smart invalidation** - Automatically detects when inputs change

### Natural File Sorting
1. **Correct slide order** - Slides appear in proper sequence (1, 2, 3, ..., 10, 11)
2. **Automatic verification** - System checks that slide numbers match between images and audio
3. **Flexible naming** - Works with both padded (01, 02) and unpadded (1, 2) numbers
4. **Error prevention** - Prevents wrong slide-audio pairing due to sorting issues