#!/usr/bin/env python3
"""
Example script demonstrating video synthesis functionality.

This script shows how to use the video synthesis service to combine
slide images with audio files into a presentation video.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Tuple

from core.domain.video_synthesis import VideoSynthesisRequest, VideoConfig
from services.video_synthesis import (
    VideoSynthesisService, VideoConfigManager, ProgressReporter
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_slide_audio_pairs() -> List[Tuple[Path, Path]]:
    """
    Create sample slide-audio pairs for demonstration.
    
    Note: This function assumes you have sample files in the examples directory.
    In a real scenario, you would provide actual slide images and audio files.
    
    Returns:
        List of (slide_image_path, audio_file_path) tuples
    """
    examples_dir = Path(__file__).parent
    
    # Sample slide-audio pairs
    # Replace these with actual file paths for testing
    pairs = [
        (examples_dir / "sample_slides" / "slide_01.png", examples_dir / "sample_audio" / "audio_01.mp3"),
        (examples_dir / "sample_slides" / "slide_02.png", examples_dir / "sample_audio" / "audio_02.mp3"),
        (examples_dir / "sample_slides" / "slide_03.png", examples_dir / "sample_audio" / "audio_03.mp3"),
    ]
    
    # Filter to only existing files
    existing_pairs = []
    for slide_path, audio_path in pairs:
        if slide_path.exists() and audio_path.exists():
            existing_pairs.append((slide_path, audio_path))
        else:
            logger.warning(f"Sample files not found: {slide_path}, {audio_path}")
    
    return existing_pairs


def create_video_configurations() -> dict:
    """
    Create different video configuration examples.
    
    Returns:
        Dictionary of configuration examples
    """
    config_manager = VideoConfigManager()
    
    configurations = {
        "default": config_manager.create_default_config(),
        "hd": config_manager.create_hd_config(),
        "4k": config_manager.create_4k_config(),
        "web_optimized": config_manager.create_web_optimized_config(),
        "custom": VideoConfig(
            resolution=(1280, 720),
            fps=24,
            video_codec="libx264",
            audio_codec="aac",
            video_bitrate="1.5M",
            audio_bitrate="128k",
            output_format="mp4",
            fade_duration=0.3
        )
    }
    
    return configurations


async def example_basic_video_synthesis():
    """Example of basic video synthesis."""
    print("\n=== Basic Video Synthesis Example ===")
    
    # Get sample slide-audio pairs
    slide_audio_pairs = create_sample_slide_audio_pairs()
    
    if not slide_audio_pairs:
        print("No sample files found. Please create sample slides and audio files.")
        print("Expected structure:")
        print("  examples/sample_slides/slide_01.png")
        print("  examples/sample_audio/audio_01.mp3")
        return
    
    # Create output path
    output_path = Path("output") / "example_presentation.mp4"
    output_path.parent.mkdir(exist_ok=True)
    
    # Create video configuration
    config_manager = VideoConfigManager()
    video_config = config_manager.create_default_config()
    
    # Create synthesis request
    slide_images = [pair[0] for pair in slide_audio_pairs]
    audio_files = [pair[1] for pair in slide_audio_pairs]
    
    request = VideoSynthesisRequest(
        slide_images=slide_images,
        audio_files=audio_files,
        output_path=output_path,
        config=video_config,
        presentation_id="example_presentation"
    )
    
    # Create progress reporter
    progress_reporter = ProgressReporter(show_detailed=True)
    
    # Initialize video synthesis service
    video_service = VideoSynthesisService()
    
    print(f"Synthesizing video with {len(slide_images)} slides...")
    
    # Synthesize video
    result = video_service.synthesize_video(
        request,
        progress_callback=progress_reporter.on_progress_update
    )
    
    # Report results
    if result.success:
        print(f"\n✓ Video synthesis completed!")
        print(f"  Output: {result.output_path}")
        print(f"  Duration: {result.duration_seconds:.2f} seconds")
        print(f"  File size: {result.get_file_size_mb():.2f} MB")
        print(f"  Processing time: {result.processing_time_seconds:.2f} seconds")
    else:
        print(f"\n✗ Video synthesis failed: {result.error_message}")


async def example_configuration_comparison():
    """Example comparing different video configurations."""
    print("\n=== Configuration Comparison Example ===")
    
    # Get sample slide-audio pairs
    slide_audio_pairs = create_sample_slide_audio_pairs()
    
    if not slide_audio_pairs:
        print("No sample files found for configuration comparison.")
        return
    
    # Get different configurations
    configurations = create_video_configurations()
    
    # Create video synthesis service
    video_service = VideoSynthesisService()
    
    # Test each configuration
    for config_name, video_config in configurations.items():
        print(f"\nTesting {config_name} configuration:")
        
        # Display configuration summary
        config_manager = VideoConfigManager()
        summary = config_manager.get_config_summary(video_config)
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Create output path
        output_path = Path("output") / f"example_{config_name}.mp4"
        output_path.parent.mkdir(exist_ok=True)
        
        # Create synthesis request
        slide_images = [pair[0] for pair in slide_audio_pairs]
        audio_files = [pair[1] for pair in slide_audio_pairs]
        
        request = VideoSynthesisRequest(
            slide_images=slide_images,
            audio_files=audio_files,
            output_path=output_path,
            config=video_config,
            presentation_id=f"example_{config_name}"
        )
        
        # Synthesize video (without detailed progress for comparison)
        result = video_service.synthesize_video(request)
        
        if result.success:
            print(f"  ✓ Success: {result.get_file_size_mb():.2f} MB, {result.processing_time_seconds:.2f}s")
        else:
            print(f"  ✗ Failed: {result.error_message}")


def example_cli_usage():
    """Example of CLI usage for video synthesis."""
    print("\n=== CLI Usage Examples ===")
    
    print("Basic video synthesis (with separate directories):")
    print("  python main.py --synthesize-video \\")
    print("    --slides-dir path/to/visuals_directory \\")
    print("    --audio-dir path/to/speech_directory \\")
    print("    --video-output output/presentation.mp4")
    
    print("\nWith example directories:")
    print("  python main.py --synthesize-video \\")
    print("    --slides-dir examples/sample_slides \\")
    print("    --audio-dir examples/sample_audio \\")
    print("    --video-output output/presentation.mp4")
    
    print("\nWith custom configuration:")
    print("  python main.py --synthesize-video \\")
    print("    --slides-dir path/to/visuals_directory \\")
    print("    --video-output output/presentation_hd.mp4 \\")
    print('    --video-config \'{"resolution": [1280, 720], "video_bitrate": "1.5M"}\'')
    
    print("\nWith configuration file:")
    print("  python main.py --synthesize-video \\")
    print("    --slides-dir path/to/visuals_directory \\")
    print("    --video-output output/presentation_custom.mp4 \\")
    print("    --video-config examples/video_config.json")
    
    print("\nUsing with style-config workflow:")
    print("  # First generate presentation with visuals and TTS")
    print("  ./run.sh --style-config hkcomic")
    print("  # Then synthesize video from the generated directories")
    print("  python main.py --synthesize-video \\")
    print("    --slides-dir generate/hkcomic/presentation_en_visuals \\")
    print("    --audio-dir generate/hkcomic/presentation_en_speech \\")
    print("    --video-output generate/hkcomic/presentation_video.mp4")
    
    print("\n=== Cache Management ===")
    print("View cache statistics:")
    print("  python main.py --video-cache-stats")
    
    print("\nClear cache (all files):")
    print("  python main.py --video-clear-cache 0")
    
    print("\nClear cache (files older than 7 days):")
    print("  python main.py --video-clear-cache 7")
    
    print("\nNote: Caching is enabled by default and stores video segments")
    print("in ./cache/video_synthesis/ to speed up reruns with same content.")


def create_sample_config_file():
    """Create a sample video configuration file."""
    print("\n=== Creating Sample Configuration File ===")
    
    config_data = {
        "resolution": [1920, 1080],
        "fps": 30,
        "video_codec": "libx264",
        "audio_codec": "aac",
        "video_bitrate": "2M",
        "audio_bitrate": "128k",
        "output_format": "mp4",
        "fade_duration": 0.5
    }
    
    config_path = Path("examples") / "video_config.json"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"Sample configuration file created: {config_path}")
    print("Contents:")
    print(json.dumps(config_data, indent=2))


async def example_integration_with_presentation():
    """Example of integrating video synthesis with presentation processing."""
    print("\n=== Integration with Presentation Processing ===")
    
    try:
        from config.config import Config
        from services.video_synthesis.integration import VideoSynthesisIntegration
        from core.domain.presentation import Presentation
        from pathlib import Path
        
        # Create a sample config with video synthesis enabled
        config = Config(
            pptx_path="examples/sample.pptx",
            pdf_path="examples/sample.pdf",
            enable_video_synthesis=True,
            video_synthesis_config={
                "resolution": [1280, 720],
                "video_bitrate": "1.5M"
            }
        )
        
        # Create integration
        integration = VideoSynthesisIntegration(config)
        
        # Check status
        status = integration.get_video_synthesis_status()
        print("Video synthesis status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Example of creating video from presentation (would need actual files)
        print("\nExample integration workflow:")
        print("1. Process presentation to generate speaker notes and visuals:")
        print("   ./run.sh --style-config hkcomic")
        print("2. TTS audio and slide images are now in the same visuals directory")
        print("3. Use video synthesis to combine slides and audio:")
        print("   integration.create_video_from_visuals_directory(presentation)")
        print("4. Output final presentation video")
        
        # Show the new convenience method
        print("\nConvenience method for same-directory workflow:")
        print("video_path = integration.create_video_from_visuals_directory(presentation)")
        print("# This automatically uses the visuals directory for both slides and audio")
        
    except ImportError as e:
        print(f"Integration example requires additional dependencies: {e}")


async def main():
    """Main example function."""
    print("Video Synthesis Examples")
    print("=" * 50)
    
    # Create sample configuration file
    create_sample_config_file()
    
    # Show CLI usage examples
    example_cli_usage()
    
    # Try basic video synthesis (if sample files exist)
    await example_basic_video_synthesis()
    
    # Try configuration comparison (if sample files exist)
    await example_configuration_comparison()
    
    # Show integration example
    await example_integration_with_presentation()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo test with real files:")
    print("1. Create examples/sample_slides/ directory with PNG/JPG images")
    print("2. Create examples/sample_audio/ directory with MP3 files")
    print("3. Ensure file names match (slide_01.png with audio_01.mp3, etc.)")
    print("4. Run this script again")


if __name__ == "__main__":
    asyncio.run(main())