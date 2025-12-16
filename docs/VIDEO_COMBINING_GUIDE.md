# Video Synthesis with MoviePy

This guide covers video synthesis and combining using MoviePy in this project. The video synthesis system now uses MoviePy instead of FFmpeg for all video processing operations.

## Installation

MoviePy has been added to the requirements and is now the primary video processing engine. Install it with:

```bash
pip install -r requirements.txt
```

Or install MoviePy directly:

```bash
pip install moviepy
```

## Video Synthesis (Main Workflow)

The main video synthesis workflow now uses MoviePy for creating videos from slide images and audio files:

```bash
# This now uses MoviePy internally
./run.sh --style-config hkcomic
```

Or directly:

```bash
python main.py --synthesize-video \
  --slides-dir path/to/visuals \
  --audio-dir path/to/speech \
  --video-output output.mp4
```

## Basic Usage

### Simple Two-Video Combination

```python
from moviepy.editor import concatenate_videoclips, VideoFileClip

# Load two video files
clip1 = VideoFileClip("video1.mp4")
clip2 = VideoFileClip("video2.mp4")

# Concatenate the videos
final_clip = concatenate_videoclips([clip1, clip2])

# Save the merged video
final_clip.write_videofile("output.mp4")

# Clean up (important!)
clip1.close()
clip2.close()
final_clip.close()
```

### Multiple Videos with Error Handling

```python
from pathlib import Path
from moviepy.editor import VideoFileClip, concatenate_videoclips

def combine_videos_safe(video_paths, output_path):
    clips = []
    
    try:
        # Load all clips
        for video_path in video_paths:
            if Path(video_path).exists():
                clip = VideoFileClip(video_path)
                clips.append(clip)
        
        # Combine and save
        if clips:
            final_clip = concatenate_videoclips(clips)
            final_clip.write_videofile(output_path)
            final_clip.close()
        
    finally:
        # Always clean up
        for clip in clips:
            clip.close()

# Usage
video_files = ["video1.mp4", "video2.mp4", "video3.mp4"]
combine_videos_safe(video_files, "combined.mp4")
```

## Using the Project's Video Synthesis Service

The `VideoSynthesisService` now includes a `combine_videos` method:

```python
from pathlib import Path
from services.video_synthesis.video_synthesis_service import VideoSynthesisService

# Create service
service = VideoSynthesisService()

# Combine videos
video_paths = [Path("video1.mp4"), Path("video2.mp4")]
output_path = Path("combined_output.mp4")

result = service.combine_videos(video_paths, output_path)

if result.success:
    print(f"Success! Combined video: {result.output_path}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print(f"File size: {result.file_size_bytes / 1024 / 1024:.1f} MB")
else:
    print(f"Failed: {result.error_message}")
```

## Command Line Utility

Use the standalone video combiner utility:

```bash
# Basic usage
python utils/video_combiner.py video1.mp4 video2.mp4 -o combined.mp4

# Multiple videos
python utils/video_combiner.py video1.mp4 video2.mp4 video3.mp4 -o output.mp4

# Quiet mode
python utils/video_combiner.py video1.mp4 video2.mp4 -o output.mp4 --quiet
```

## Benefits of MoviePy Integration

### Advantages over FFmpeg
- **Pure Python**: No external binary dependencies
- **Better error handling**: More descriptive Python exceptions
- **Memory management**: Automatic cleanup of video clips
- **Cross-platform**: Works consistently across operating systems
- **Easier transitions**: Built-in support for fades and crossfades
- **Flexible processing**: Easy to add custom effects and filters

### Performance Considerations
- MoviePy loads entire videos into memory for processing
- Better for moderate-sized videos (under 1GB)
- Automatic multi-threading for some operations
- Built-in progress tracking and cancellation support

## Advanced Features

### Custom Codec Settings

```python
final_clip.write_videofile(
    "output.mp4",
    codec='libx264',           # Video codec
    audio_codec='aac',         # Audio codec
    bitrate='5000k',           # Video bitrate
    fps=30,                    # Frame rate
    preset='medium'            # Encoding speed vs quality
)
```

### Adding Transitions

```python
from moviepy.video.fx import fadein, fadeout

# Add fade effects to each clip
clip1 = VideoFileClip("video1.mp4").fx(fadein, 1).fx(fadeout, 1)
clip2 = VideoFileClip("video2.mp4").fx(fadein, 1).fx(fadeout, 1)

# Concatenate with overlap for smooth transitions
final_clip = concatenate_videoclips([clip1, clip2], padding=-0.5, method="compose")
```

### Resizing Videos to Match

```python
from moviepy.video.fx import resize

# Resize all clips to the same dimensions
target_size = (1920, 1080)
clips = []

for video_path in video_paths:
    clip = VideoFileClip(video_path)
    clip = clip.fx(resize, target_size)
    clips.append(clip)

final_clip = concatenate_videoclips(clips)
```

## Performance Tips

1. **Always close clips** to free memory:
   ```python
   clip.close()
   ```

2. **Use appropriate codecs** for your needs:
   - `libx264`: Good quality, widely compatible
   - `libx265`: Better compression, slower encoding
   - `libvpx-vp9`: Good for web, open source

3. **Set reasonable bitrates**:
   ```python
   # For 1080p video
   final_clip.write_videofile("output.mp4", bitrate='5000k')
   ```

4. **Use temp files for large operations**:
   ```python
   final_clip.write_videofile(
       "output.mp4",
       temp_audiofile='temp-audio.m4a',
       remove_temp=True
   )
   ```

## Common Issues

### Memory Usage
- MoviePy loads entire videos into memory
- For large files, consider processing in chunks
- Always close clips when done

### Audio Sync
- Ensure all input videos have audio tracks
- Use consistent audio codecs
- Consider re-encoding audio if sync issues occur

### Format Compatibility
- Stick to common formats (MP4, AVI, MOV)
- Use consistent frame rates when possible
- Test with small files first

## Examples

See the `examples/combine_videos_example.py` file for complete working examples.

## Troubleshooting

### MoviePy Not Found
```bash
pip install moviepy
```

### FFmpeg Issues
MoviePy requires FFmpeg. Install it:
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/

### Memory Errors
- Process smaller files
- Close clips promptly
- Use lower quality settings for testing