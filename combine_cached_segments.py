#!/usr/bin/env python3
"""
Combine cached video segments for the cybersecurity presentation.
This bypasses the segment creation and just combines existing MP4 files.
File-based caching only - no JSON metadata.
"""

from pathlib import Path
from services.video_synthesis.file_manager import VideoFileManager
from services.video_synthesis.video_synthesis_service import VideoSynthesisService

def find_matching_segments():
    """Find cached segments by matching slide/audio pairs with cached files (file-based only)."""
    
    slides_dir = Path("notes/hkcomic/generate/Module 4a Cybersecurity Essentials - Information Security Concepts_en_visuals")
    audio_dir = Path("notes/hkcomic/generate/Module 4a Cybersecurity Essentials - Information Security Concepts_en_speech")
    cache_dir = Path("cache/video_synthesis")
    
    # Get slide and audio files
    slide_files = sorted(slides_dir.glob("*.png"))
    audio_files = sorted(audio_dir.glob("*.mp3"))
    
    print(f"📁 Found {len(slide_files)} slides and {len(audio_files)} audio files")
    
    # Find cached segments by checking actual files (no JSON metadata)
    matching_segments = []
    
    for i, (slide_file, audio_file) in enumerate(zip(slide_files, audio_files)):
        # Look for cached segment files that match this slide index
        # Pattern: segment_*.mp4 or slide_*.mp4
        possible_segments = list(cache_dir.glob(f"segment_{i:03d}_*.mp4")) + \
                          list(cache_dir.glob(f"slide_{i}_*.mp4")) + \
                          list(cache_dir.glob(f"segment_{i}_*.mp4"))
        
        if possible_segments:
            # Use the first matching segment file
            segment_file = possible_segments[0]
            matching_segments.append({
                'index': i,
                'slide': slide_file,
                'audio': audio_file,
                'segment': segment_file
            })
            print(f"✅ Found cached segment {i+1}: {segment_file.name}")
        else:
            print(f"❌ No cached segment found for slide {i+1}: {slide_file.name}")
    
    return matching_segments

def combine_segments_with_moviepy(segments, output_path):
    """Combine segments using MoviePy."""
    try:
        from moviepy import VideoFileClip, concatenate_videoclips
    except ImportError:
        print("❌ MoviePy not available")
        return False
    
    print(f"🎬 Combining {len(segments)} segments with MoviePy...")
    
    clips = []
    total_duration = 0
    
    try:
        # Load all segments
        for i, segment_info in enumerate(segments):
            segment_path = segment_info['segment']
            print(f"📼 Loading segment {i+1}/{len(segments)}: {segment_path.name}")
            
            clip = VideoFileClip(str(segment_path))
            clips.append(clip)
            total_duration += clip.duration
        
        print(f"⏱️  Total duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
        
        # Concatenate all clips
        print("🔗 Concatenating clips...")
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Write final video
        print(f"💾 Writing final video to: {output_path}")
        final_clip.write_videofile(str(output_path))
        
        # Clean up
        final_clip.close()
        for clip in clips:
            clip.close()
        
        print("✅ Video combination completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error combining segments: {e}")
        # Clean up clips
        try:
            if 'final_clip' in locals():
                final_clip.close()
            for clip in clips:
                clip.close()
        except:
            pass
        return False

def main():
    print("🎥 Cached Segment Combiner")
    print("=" * 50)
    
    # Find matching segments
    segments = find_matching_segments()
    
    if not segments:
        print("❌ No matching cached segments found")
        return False
    
    if len(segments) != 46:
        print(f"⚠️  Expected 46 segments, found {len(segments)}")
        print("Some segments may be missing from cache")
    
    # Sort segments by index
    segments.sort(key=lambda x: x['index'])
    
    # Output path
    output_path = Path("notes/hkcomic/generate/Module_4a_Cybersecurity_Essentials__Information_Security_Concepts_en_hkcomic.mp4")
    
    # Combine segments
    success = combine_segments_with_moviepy(segments, output_path)
    
    if success:
        if output_path.exists():
            file_size = output_path.stat().st_size / (1024 * 1024)
            print(f"📊 Final video: {output_path}")
            print(f"📊 File size: {file_size:.2f} MB")
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)