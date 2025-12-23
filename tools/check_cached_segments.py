#!/usr/bin/env python3
"""
Check existing cached video segments to see what can be reused.
"""

import argparse
from pathlib import Path


def check_cached_segments(base_dir, presentation_name, language):
    """Check cached segments for a specific presentation and language."""
    
    # Construct expected cache directory path
    cache_dir_name = f"{presentation_name}_{language}_segments"
    cache_dir = Path(base_dir) / cache_dir_name
    
    print(f"🔍 Checking cached segments for: {presentation_name} ({language})")
    print(f"📁 Cache directory: {cache_dir}")
    
    if not cache_dir.exists():
        print("❌ Cache directory does not exist")
        return 0, 0
    
    # Find cached segment files
    segment_files = list(cache_dir.glob("slide_*.mp4")) + list(cache_dir.glob("slide_*.webm"))
    
    if not segment_files:
        print("❌ No cached segments found")
        return 0, 0
    
    # Sort by filename for better display
    segment_files.sort()
    
    total_size = 0
    print(f"\n✅ Found {len(segment_files)} cached segments:")
    
    for i, segment_file in enumerate(segment_files[:10]):  # Show first 10
        try:
            size_mb = segment_file.stat().st_size / (1024 * 1024)
            total_size += size_mb
            print(f"  {i+1:3d}. {segment_file.name} ({size_mb:.2f} MB)")
        except Exception as e:
            print(f"  {i+1:3d}. {segment_file.name} (error: {e})")
    
    if len(segment_files) > 10:
        # Calculate remaining size
        for segment_file in segment_files[10:]:
            try:
                size_mb = segment_file.stat().st_size / (1024 * 1024)
                total_size += size_mb
            except:
                pass
        print(f"  ... and {len(segment_files) - 10} more segments")
    
    print(f"\n📊 Total: {len(segment_files)} segments, {total_size:.2f} MB")
    
    return len(segment_files), total_size


def main():
    parser = argparse.ArgumentParser(description='Check cached video segments')
    parser.add_argument('--base-dir', 
                       default='/mnt/hgfs/VM Share/ite3001/hkcomic/generate',
                       help='Base directory for cache')
    parser.add_argument('--presentation', 
                       default='Introduction to Programming Lecture',
                       help='Presentation name')
    parser.add_argument('--language', 
                       default='zh-CN',
                       help='Language code')
    parser.add_argument('--all-languages', action='store_true',
                       help='Check all common languages')
    
    args = parser.parse_args()
    
    if args.all_languages:
        languages = ['en', 'zh-CN', 'yue-HK']
        total_segments = 0
        total_size = 0
        
        for lang in languages:
            segments, size = check_cached_segments(args.base_dir, args.presentation, lang)
            total_segments += segments
            total_size += size
            print()
        
        print(f"🎯 Overall Summary:")
        print(f"   Total cached segments: {total_segments}")
        print(f"   Total cache size: {total_size:.2f} MB")
        
    else:
        check_cached_segments(args.base_dir, args.presentation, args.language)


if __name__ == '__main__':
    main()