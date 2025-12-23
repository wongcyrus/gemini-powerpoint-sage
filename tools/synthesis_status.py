#!/usr/bin/env python3
"""
Show current video synthesis status - disk usage, existing videos, running processes.
"""

import subprocess
import sys
from pathlib import Path
import yaml


def check_disk_usage():
    """Check disk usage for key directories."""
    print("💾 Disk Usage:")
    
    dirs_to_check = ['/tmp', '/mnt/hgfs/VM Share/ite3001/hkcomic/generate', '.']
    
    for dir_path in dirs_to_check:
        try:
            if Path(dir_path).exists():
                result = subprocess.run(['df', '-h', dir_path], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        header = lines[0]
                        data = lines[1]
                        parts = data.split()
                        if len(parts) >= 5:
                            used_percent = parts[4]
                            available = parts[3]
                            print(f"  {dir_path}: {used_percent} used, {available} available")
                            
                            # Warning for high usage
                            usage_num = int(used_percent.rstrip('%'))
                            if usage_num > 90:
                                print(f"    ⚠️  CRITICAL: Very high disk usage!")
                            elif usage_num > 80:
                                print(f"    ⚠️  WARNING: High disk usage")
        except Exception as e:
            print(f"  {dir_path}: Error checking - {e}")
    print()


def check_running_processes():
    """Check for running video synthesis processes."""
    print("🔄 Running Processes:")
    
    try:
        # Check for main.py synthesis processes
        result = subprocess.run(['pgrep', '-f', 'main.py.*synthesize-video'], 
                               capture_output=True, text=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"  📹 Video synthesis: {len(pids)} processes running")
            for pid in pids:
                print(f"    PID {pid}")
        else:
            print("  📹 Video synthesis: No processes running")
        
        # Check for FFmpeg processes
        result = subprocess.run(['pgrep', '-f', 'ffmpeg'], 
                               capture_output=True, text=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"  🎬 FFmpeg: {len(pids)} processes running")
        else:
            print("  🎬 FFmpeg: No processes running")
            
    except Exception as e:
        print(f"  Error checking processes: {e}")
    
    print()


def check_existing_videos():
    """Check existing videos."""
    print("🎥 Existing Videos:")
    
    base_dir = Path('/mnt/hgfs/VM Share/ite3001/hkcomic/generate')
    
    if not base_dir.exists():
        print("  Base directory not found")
        return
    
    video_files = list(base_dir.glob('*.mp4'))
    
    if not video_files:
        print("  No video files found")
        return
    
    total_size = 0
    for video_file in video_files:
        try:
            size_gb = video_file.stat().st_size / (1024**3)
            total_size += size_gb
            print(f"  ✅ {video_file.name} ({size_gb:.2f} GB)")
        except Exception as e:
            print(f"  ❌ {video_file.name} (error: {e})")
    
    print(f"  📊 Total: {len(video_files)} videos, {total_size:.2f} GB")
    print()


def check_temp_files():
    """Check for temporary files."""
    print("🗂️  Temporary Files:")
    
    temp_dirs = [Path('/tmp'), Path('.')]
    temp_patterns = ['video_synthesis_*', 'segment_*', 'chunk_*']
    
    total_temp_files = 0
    total_temp_size = 0
    
    for temp_dir in temp_dirs:
        if not temp_dir.exists():
            continue
            
        dir_temp_files = 0
        dir_temp_size = 0
        
        for pattern in temp_patterns:
            for item in temp_dir.glob(pattern):
                if item.is_file():
                    try:
                        size = item.stat().st_size
                        dir_temp_files += 1
                        dir_temp_size += size
                    except:
                        pass
                elif item.is_dir():
                    # Count files in temp directory
                    try:
                        for sub_item in item.rglob('*'):
                            if sub_item.is_file():
                                size = sub_item.stat().st_size
                                dir_temp_files += 1
                                dir_temp_size += size
                    except:
                        pass
        
        if dir_temp_files > 0:
            print(f"  {temp_dir}: {dir_temp_files} files ({dir_temp_size / (1024**2):.2f} MB)")
            total_temp_files += dir_temp_files
            total_temp_size += dir_temp_size
    
    if total_temp_files == 0:
        print("  ✅ No temporary files found")
    else:
        print(f"  📊 Total: {total_temp_files} temp files ({total_temp_size / (1024**2):.2f} MB)")
        if total_temp_size > 100 * 1024 * 1024:  # > 100MB
            print("  ⚠️  Consider running cleanup: python tools/cleanup_temp_files.py")
    
    print()


def check_cached_segments():
    """Check cached segments."""
    print("🎬 Cached Segments:")
    
    base_dir = Path('/mnt/hgfs/VM Share/ite3001/hkcomic/generate')
    
    if not base_dir.exists():
        print("  Base directory not found")
        return
    
    # Look for segment cache directories
    cache_dirs = list(base_dir.glob('*_segments'))
    
    if not cache_dirs:
        print("  No cached segments found")
        return
    
    total_segments = 0
    total_size = 0
    
    for cache_dir in cache_dirs:
        try:
            segments = list(cache_dir.glob('slide_*.mp4')) + list(cache_dir.glob('slide_*.webm'))
            if segments:
                dir_size = sum(s.stat().st_size for s in segments if s.exists()) / (1024**2)
                total_segments += len(segments)
                total_size += dir_size
                
                # Extract language from directory name
                lang = cache_dir.name.split('_')[-2] if '_' in cache_dir.name else 'unknown'
                print(f"  {lang}: {len(segments)} segments ({dir_size:.0f} MB)")
        except Exception as e:
            print(f"  {cache_dir.name}: Error - {e}")
    
    if total_segments > 0:
        print(f"  📊 Total: {total_segments} segments ({total_size:.0f} MB)")
        print(f"  💡 Cached segments will be reused to save processing time")
    
    print()


def main():
    print("🔍 Video Synthesis Status Check")
    print("=" * 50)
    
    check_disk_usage()
    check_running_processes()
    check_existing_videos()
    check_cached_segments()
    check_temp_files()
    
    print("🛠️  Available Tools:")
    print("  python tools/monitor_disk_usage.py          - Check disk usage")
    print("  python tools/check_existing_videos.py       - Check existing videos")
    print("  python tools/cleanup_temp_files.py --dry-run - Preview cleanup")
    print("  python tools/kill_hanging_synthesis.py      - Kill hanging processes")


if __name__ == '__main__':
    main()