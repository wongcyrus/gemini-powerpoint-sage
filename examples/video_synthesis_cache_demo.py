#!/usr/bin/env python3
"""
Demo script showing video synthesis caching functionality.

This script demonstrates how caching speeds up video synthesis reruns
by reusing previously generated video segments.
"""

import time
from pathlib import Path
from services.video_synthesis.video_synthesis_service import VideoSynthesisService
from services.video_synthesis.video_config_manager import VideoConfigManager
from core.domain.video_synthesis import VideoSynthesisRequest

def demo_caching_speedup():
    """Demonstrate caching speedup by running synthesis twice."""
    
    print("Video Synthesis Caching Demo")
    print("=" * 50)
    
    # Define paths (using the existing presentation files)
    slides_dir = Path("notes/hkcomic/generate/Module 4b Cybersecurity Essentials - Security and Risk Management Framework_en_visuals")
    audio_dir = Path("notes/hkcomic/generate/Module 4b Cybersecurity Essentials - Security and Risk Management Framework_en_speech")
    
    if not slides_dir.exists() or not audio_dir.exists():
        print("Error: Sample presentation files not found.")
        print("Please run the presentation processing first:")
        print("  ./run.sh --style-config hkcomic")
        return
    
    # Find slide images and audio files (limit to first 5 for demo)
    slide_images = sorted(list(slides_dir.glob("*.png")))[:5]
    audio_files = sorted(list(audio_dir.glob("*.mp3")))[:5]
    
    if len(slide_images) != len(audio_files):
        print(f"Error: Mismatch in file counts - {len(slide_images)} images vs {len(audio_files)} audio files")
        return
    
    print(f"Using {len(slide_images)} slides for caching demo")
    
    # Create video configuration
    config_manager = VideoConfigManager()
    video_config = config_manager.create_default_config()
    
    # Create video synthesis service
    video_service = VideoSynthesisService()
    
    # First run - no cache
    print("\n" + "=" * 50)
    print("FIRST RUN (No Cache)")
    print("=" * 50)
    
    output_path_1 = Path("output/cache_demo_run1.mp4")
    output_path_1.parent.mkdir(exist_ok=True)
    
    request_1 = VideoSynthesisRequest(
        slide_images=slide_images,
        audio_files=audio_files,
        output_path=output_path_1,
        config=video_config,
        presentation_id="cache_demo_run1"
    )
    
    start_time_1 = time.time()
    result_1 = video_service.synthesize_video(request_1)
    end_time_1 = time.time()
    
    if result_1.success:
        print(f"✓ First run completed in {end_time_1 - start_time_1:.2f} seconds")
        print(f"  Output: {result_1.output_path}")
        print(f"  File size: {result_1.get_file_size_mb():.2f} MB")
    else:
        print(f"✗ First run failed: {result_1.error_message}")
        return
    
    # Second run - with cache
    print("\n" + "=" * 50)
    print("SECOND RUN (With Cache)")
    print("=" * 50)
    
    output_path_2 = Path("output/cache_demo_run2.mp4")
    
    request_2 = VideoSynthesisRequest(
        slide_images=slide_images,
        audio_files=audio_files,
        output_path=output_path_2,
        config=video_config,
        presentation_id="cache_demo_run2"
    )
    
    start_time_2 = time.time()
    result_2 = video_service.synthesize_video(request_2)
    end_time_2 = time.time()
    
    if result_2.success:
        print(f"✓ Second run completed in {end_time_2 - start_time_2:.2f} seconds")
        print(f"  Output: {result_2.output_path}")
        print(f"  File size: {result_2.get_file_size_mb():.2f} MB")
    else:
        print(f"✗ Second run failed: {result_2.error_message}")
        return
    
    # Show speedup
    speedup = (end_time_1 - start_time_1) / (end_time_2 - start_time_2)
    time_saved = (end_time_1 - start_time_1) - (end_time_2 - start_time_2)
    
    print("\n" + "=" * 50)
    print("CACHING RESULTS")
    print("=" * 50)
    print(f"First run time:  {end_time_1 - start_time_1:.2f} seconds")
    print(f"Second run time: {end_time_2 - start_time_2:.2f} seconds")
    print(f"Time saved:      {time_saved:.2f} seconds")
    print(f"Speedup:         {speedup:.2f}x faster")
    
    if speedup > 1.5:
        print("🚀 Significant speedup achieved with caching!")
    elif speedup > 1.1:
        print("✓ Moderate speedup achieved with caching")
    else:
        print("⚠️  Limited speedup - cache may not be working optimally")

def show_cache_management():
    """Show cache management commands."""
    print("\n" + "=" * 50)
    print("CACHE MANAGEMENT COMMANDS")
    print("=" * 50)
    
    print("View cache statistics:")
    print("  python main.py --video-cache-stats")
    
    print("\nClear entire cache:")
    print("  python main.py --video-clear-cache 0")
    
    print("\nClear cache files older than 7 days:")
    print("  python main.py --video-clear-cache 7")
    
    print("\nCache location:")
    print("  ./cache/video_synthesis/")

if __name__ == "__main__":
    demo_caching_speedup()
    show_cache_management()