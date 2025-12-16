#!/usr/bin/env python3
"""
Simple video combiner utility using MoviePy.

This utility provides a simple interface for combining multiple video files
into a single output video using MoviePy's concatenate_videoclips function.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

try:
    from moviepy import VideoFileClip, concatenate_videoclips
except ImportError:
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips
    except ImportError:
        print("Error: MoviePy is required. Install it with: pip install moviepy")
        sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def combine_videos(
    input_videos: List[str], 
    output_path: str,
    verbose: bool = True
) -> bool:
    """
    Combine multiple video files into a single video.
    
    Args:
        input_videos: List of paths to input video files
        output_path: Path for the output combined video
        verbose: Whether to show detailed progress
        
    Returns:
        True if successful, False otherwise
    """
    clips = []
    
    try:
        if verbose:
            logger.info(f"Starting video combination of {len(input_videos)} files")
        
        # Load video clips
        total_duration = 0
        for i, video_path in enumerate(input_videos):
            video_file = Path(video_path)
            
            if not video_file.exists():
                logger.error(f"Video file not found: {video_path}")
                return False
            
            if verbose:
                logger.info(f"Loading video {i+1}/{len(input_videos)}: {video_file.name}")
            
            try:
                clip = VideoFileClip(str(video_file))
                clips.append(clip)
                total_duration += clip.duration
                
                if verbose:
                    logger.info(f"  Duration: {clip.duration:.2f}s, Resolution: {clip.size}")
                    
            except Exception as e:
                logger.error(f"Failed to load video {video_path}: {e}")
                # Clean up already loaded clips
                for loaded_clip in clips:
                    loaded_clip.close()
                return False
        
        if verbose:
            logger.info(f"Total duration: {total_duration:.2f}s")
            logger.info("Concatenating video clips...")
        
        # Concatenate videos
        final_clip = concatenate_videoclips(clips)
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if verbose:
            logger.info(f"Writing combined video to: {output_path}")
        
        # Write the combined video
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            verbose=verbose,
            logger='bar' if verbose else None
        )
        
        # Clean up
        final_clip.close()
        for clip in clips:
            clip.close()
        
        if verbose:
            output_size = output_file.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Video combination completed successfully!")
            logger.info(f"Output file: {output_path} ({output_size:.1f} MB)")
        
        return True
        
    except Exception as e:
        logger.error(f"Video combination failed: {e}")
        
        # Clean up clips in case of error
        try:
            if 'final_clip' in locals():
                final_clip.close()
            for clip in clips:
                clip.close()
        except:
            pass  # Ignore cleanup errors
        
        return False


def main():
    """Command line interface for video combining."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Combine multiple video files into a single video using MoviePy"
    )
    parser.add_argument(
        'videos',
        nargs='+',
        help='Input video files to combine'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output video file path'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate input files
    for video_path in args.videos:
        if not Path(video_path).exists():
            logger.error(f"Input video not found: {video_path}")
            sys.exit(1)
    
    # Combine videos
    success = combine_videos(
        input_videos=args.videos,
        output_path=args.output,
        verbose=not args.quiet
    )
    
    if success:
        print(f"✓ Successfully combined {len(args.videos)} videos into {args.output}")
        sys.exit(0)
    else:
        print("✗ Video combination failed")
        sys.exit(1)


if __name__ == "__main__":
    main()