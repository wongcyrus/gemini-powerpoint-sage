#!/usr/bin/env python3
"""
Example script showing how to combine videos using MoviePy.

This demonstrates the basic usage pattern you provided.
"""

from pathlib import Path

try:
    from moviepy import concatenate_videoclips, VideoFileClip
except ImportError:
    from moviepy.editor import concatenate_videoclips, VideoFileClip


def basic_video_combination():
    """Basic example of combining two videos."""
    
    # Load two video files
    clip1 = VideoFileClip("video1.mp4")
    clip2 = VideoFileClip("video2.mp4")
    
    # Concatenate the videos
    final_clip = concatenate_videoclips([clip1, clip2])
    
    # Save the merged video
    final_clip.write_videofile("output.mp4")
    
    # Clean up
    clip1.close()
    clip2.close()
    final_clip.close()


def advanced_video_combination():
    """More advanced example with error handling and multiple videos."""
    
    # List of video files to combine
    video_files = ["video1.mp4", "video2.mp4", "video3.mp4"]
    output_file = "combined_output.mp4"
    
    clips = []
    
    try:
        print(f"Loading {len(video_files)} video files...")
        
        # Load all video clips
        for i, video_file in enumerate(video_files):
            video_path = Path(video_file)
            
            if not video_path.exists():
                print(f"Warning: Video file not found: {video_file}")
                continue
            
            print(f"Loading {video_file}...")
            clip = VideoFileClip(video_file)
            clips.append(clip)
            print(f"  Duration: {clip.duration:.2f}s, Size: {clip.size}")
        
        if not clips:
            print("No valid video files found!")
            return
        
        print(f"\nCombining {len(clips)} video clips...")
        
        # Concatenate all clips
        final_clip = concatenate_videoclips(clips)
        
        print(f"Writing combined video to {output_file}...")
        
        # Write the final video with specific codec settings
        final_clip.write_videofile(
            output_file,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        print(f"✓ Successfully created {output_file}")
        
        # Display final video info
        output_path = Path(output_file)
        if output_path.exists():
            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            print(f"Output file size: {file_size:.1f} MB")
            print(f"Total duration: {final_clip.duration:.2f}s")
        
    except Exception as e:
        print(f"Error during video combination: {e}")
    
    finally:
        # Clean up all clips
        try:
            if 'final_clip' in locals():
                final_clip.close()
            for clip in clips:
                clip.close()
        except:
            pass


def combine_with_transitions():
    """Example showing how to add transitions between videos."""
    
    try:
        try:
            from moviepy import VideoFileClip, concatenate_videoclips, CompositeVideoClip
        except ImportError:
            from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
        
        # Load video files
        video_files = ["video1.mp4", "video2.mp4"]
        clips = []
        
        for video_file in video_files:
            if Path(video_file).exists():
                clip = VideoFileClip(video_file)
                
                # Add fade in/out effects
                try:
                    from moviepy.video.fx.FadeIn import FadeIn
                    from moviepy.video.fx.FadeOut import FadeOut
                    clip = clip.with_effects([FadeIn(0.5), FadeOut(0.5)])
                except ImportError:
                    pass  # Skip fade effects if not available
                clips.append(clip)
        
        if clips:
            # Concatenate with smooth transitions
            final_clip = concatenate_videoclips(clips, padding=-0.5, method="compose")
            
            # Write output
            final_clip.write_videofile("output_with_transitions.mp4")
            
            # Clean up
            final_clip.close()
            for clip in clips:
                clip.close()
            
            print("✓ Created video with transitions")
        
    except ImportError:
        print("Advanced effects require additional MoviePy components")
    except Exception as e:
        print(f"Error creating transitions: {e}")


if __name__ == "__main__":
    print("MoviePy Video Combination Examples")
    print("=" * 40)
    
    # Check if example videos exist
    example_videos = ["video1.mp4", "video2.mp4"]
    available_videos = [v for v in example_videos if Path(v).exists()]
    
    if not available_videos:
        print("No example video files found.")
        print("Create some test videos or update the file paths in this script.")
        print("\nExample usage:")
        print("  from moviepy.editor import concatenate_videoclips, VideoFileClip")
        print("  clip1 = VideoFileClip('video1.mp4')")
        print("  clip2 = VideoFileClip('video2.mp4')")
        print("  final_clip = concatenate_videoclips([clip1, clip2])")
        print("  final_clip.write_videofile('output.mp4')")
    else:
        print(f"Found {len(available_videos)} example videos")
        print("\nRunning basic combination example...")
        basic_video_combination()
        
        print("\nRunning advanced combination example...")
        advanced_video_combination()
        
        print("\nRunning transitions example...")
        combine_with_transitions()