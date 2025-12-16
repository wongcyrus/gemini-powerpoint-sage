#!/usr/bin/env python3
"""
Fast video combiner using FFmpeg directly.
Much faster than MoviePy for combining existing MP4 files.
"""

import subprocess
import tempfile
from pathlib import Path

def combine_with_ffmpeg(segment_files, output_path):
    """Combine MP4 segments using FFmpeg concat demuxer (fastest method)."""
    
    print(f"🚀 Fast combining {len(segment_files)} segments with FFmpeg...")
    
    # Create temporary concat file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        concat_file = Path(f.name)
        
        # Write file list for FFmpeg concat demuxer
        for segment_file in segment_files:
            f.write(f"file '{segment_file.absolute()}'\n")
    
    try:
        # Use FFmpeg concat demuxer (fastest method for MP4 files)
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-f', 'concat',  # Use concat demuxer
            '-safe', '0',    # Allow absolute paths
            '-i', str(concat_file),  # Input concat file
            '-c', 'copy',    # Copy streams without re-encoding (fastest!)
            str(output_path)  # Output file
        ]
        
        print(f"🔧 Running: {' '.join(cmd[:6])}...")
        
        # Run FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ FFmpeg combination completed successfully!")
            return True
        else:
            print(f"❌ FFmpeg failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg timed out")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please install FFmpeg.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up concat file
        concat_file.unlink(missing_ok=True)

def main():
    print("⚡ Fast Video Combiner (FFmpeg)")
    print("=" * 40)
    
    # Get first 46 cached segments
    cache_dir = Path('cache/video_synthesis')
    segment_files = sorted(cache_dir.glob('segment_*.mp4'))[:46]
    
    if not segment_files:
        print("❌ No cached segments found")
        return False
    
    print(f"📁 Found {len(segment_files)} cached segments")
    
    # Calculate total duration quickly
    total_duration = 0
    for i, segment_file in enumerate(segment_files[:5]):  # Check first 5 for estimate
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', str(segment_file)
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                total_duration += duration
        except:
            pass
    
    estimated_total = total_duration * len(segment_files) / 5  # Estimate from first 5
    print(f"⏱️  Estimated total duration: {estimated_total/60:.1f} minutes")
    
    # Output path
    output_path = Path("notes/hkcomic/generate/Module_4a_Cybersecurity_Essentials__Information_Security_Concepts_en_hkcomic.mp4")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Combine with FFmpeg
    success = combine_with_ffmpeg(segment_files, output_path)
    
    if success and output_path.exists():
        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"🎉 Success!")
        print(f"📹 Output: {output_path}")
        print(f"📊 File size: {file_size:.2f} MB")
        return True
    else:
        print("❌ Failed to create video")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)