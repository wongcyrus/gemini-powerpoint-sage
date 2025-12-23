#!/usr/bin/env python3
"""
Check MP3 caching behavior to verify files are not being regenerated unnecessarily.
"""

import argparse
import os
from pathlib import Path
from typing import Dict, List, Tuple
import time


def get_file_info(file_path: Path) -> Dict:
    """Get file information including size and modification time."""
    try:
        stat = file_path.stat()
        return {
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'mtime_str': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime)),
            'exists': True
        }
    except Exception as e:
        return {
            'size': 0,
            'mtime': 0,
            'mtime_str': 'N/A',
            'exists': False,
            'error': str(e)
        }


def find_mp3_files(base_dir: Path, presentation_name: str, language: str) -> List[Path]:
    """Find MP3 files for a specific presentation and language."""
    speech_dir_name = f"{presentation_name}_{language}_speech"
    speech_dir = base_dir / speech_dir_name
    
    if not speech_dir.exists():
        return []
    
    mp3_files = list(speech_dir.glob("*.mp3"))
    
    # Sort using natural sorting (same as the CLI)
    def natural_sort_key(path):
        import re
        filename = path.name
        def convert(text):
            return int(text) if text.isdigit() else text.lower()
        return [convert(c) for c in re.split('([0-9]+)', filename)]
    
    return sorted(mp3_files, key=natural_sort_key)


def check_mp3_caching(base_dir: Path, presentation_name: str, language: str) -> Dict:
    """Check MP3 caching status for a presentation."""
    print(f"🔍 Checking MP3 caching for: {presentation_name} ({language})")
    
    speech_dir_name = f"{presentation_name}_{language}_speech"
    speech_dir = base_dir / speech_dir_name
    
    print(f"📁 Speech directory: {speech_dir}")
    
    if not speech_dir.exists():
        print("❌ Speech directory does not exist")
        return {'status': 'no_directory', 'files': []}
    
    mp3_files = find_mp3_files(base_dir, presentation_name, language)
    
    if not mp3_files:
        print("❌ No MP3 files found")
        return {'status': 'no_files', 'files': []}
    
    print(f"✅ Found {len(mp3_files)} MP3 files")
    
    # Analyze files
    file_info = []
    total_size = 0
    oldest_time = float('inf')
    newest_time = 0
    
    for i, mp3_file in enumerate(mp3_files):
        info = get_file_info(mp3_file)
        info['filename'] = mp3_file.name
        info['index'] = i + 1
        file_info.append(info)
        
        if info['exists']:
            total_size += info['size']
            oldest_time = min(oldest_time, info['mtime'])
            newest_time = max(newest_time, info['mtime'])
    
    # Show first 10 files
    print(f"\n📋 MP3 Files (showing first 10 of {len(file_info)}):")
    for info in file_info[:10]:
        if info['exists']:
            size_kb = info['size'] / 1024
            print(f"  {info['index']:3d}. {info['filename']} ({size_kb:.1f} KB, {info['mtime_str']})")
        else:
            print(f"  {info['index']:3d}. {info['filename']} (ERROR: {info.get('error', 'unknown')})")
    
    if len(file_info) > 10:
        print(f"  ... and {len(file_info) - 10} more files")
    
    # Summary statistics
    total_size_mb = total_size / (1024 * 1024)
    time_span = newest_time - oldest_time if oldest_time != float('inf') else 0
    
    print(f"\n📊 Summary:")
    print(f"   Total files: {len(file_info)}")
    print(f"   Total size: {total_size_mb:.2f} MB")
    
    if oldest_time != float('inf'):
        oldest_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(oldest_time))
        newest_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(newest_time))
        print(f"   Oldest file: {oldest_str}")
        print(f"   Newest file: {newest_str}")
        print(f"   Time span: {time_span / 3600:.1f} hours")
        
        # Check if files were created recently (within last hour)
        current_time = time.time()
        recent_files = [info for info in file_info if info['exists'] and (current_time - info['mtime']) < 3600]
        if recent_files:
            print(f"   ⚠️  {len(recent_files)} files were created/modified in the last hour")
            print(f"      This might indicate recent regeneration")
        else:
            print(f"   ✅ No files were modified in the last hour (good caching)")
    
    return {
        'status': 'found',
        'files': file_info,
        'total_size': total_size,
        'total_files': len(file_info),
        'oldest_time': oldest_time if oldest_time != float('inf') else None,
        'newest_time': newest_time if newest_time > 0 else None
    }


def analyze_file_matching(base_dir: Path, presentation_name: str, language: str) -> Dict:
    """Analyze how MP3 files match with slide images."""
    print(f"\n🔍 Analyzing file matching for: {presentation_name} ({language})")
    
    # Find directories
    speech_dir_name = f"{presentation_name}_{language}_speech"
    visuals_dir_name = f"{presentation_name}_{language}_visuals"
    
    speech_dir = base_dir / speech_dir_name
    visuals_dir = base_dir / visuals_dir_name
    
    if not speech_dir.exists():
        print(f"❌ Speech directory not found: {speech_dir}")
        return {'status': 'no_speech_dir'}
    
    if not visuals_dir.exists():
        print(f"❌ Visuals directory not found: {visuals_dir}")
        return {'status': 'no_visuals_dir'}
    
    # Get files
    mp3_files = find_mp3_files(base_dir, presentation_name, language)
    
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        image_files.extend(visuals_dir.glob(ext))
    
    # Sort using natural sorting
    def natural_sort_key(path):
        import re
        filename = path.name
        def convert(text):
            return int(text) if text.isdigit() else text.lower()
        return [convert(c) for c in re.split('([0-9]+)', filename)]
    
    image_files = sorted(image_files, key=natural_sort_key)
    
    # Extract slide numbers from images
    needed_slide_numbers = set()
    for img in image_files:
        try:
            import re
            match = re.search(r'slide_(\d+)', img.name)
            if match:
                needed_slide_numbers.add(int(match.group(1)))
        except:
            pass
    
    # Categorize MP3 files
    needed_mp3 = []
    excess_mp3 = []
    
    for mp3 in mp3_files:
        try:
            import re
            match = re.search(r'slide_(\d+)', mp3.name)
            if match:
                slide_num = int(match.group(1))
                if slide_num in needed_slide_numbers:
                    needed_mp3.append((mp3, slide_num))
                else:
                    excess_mp3.append((mp3, slide_num))
            else:
                excess_mp3.append((mp3, None))
        except:
            excess_mp3.append((mp3, None))
    
    print(f"📊 File Analysis:")
    print(f"   Image files: {len(image_files)}")
    print(f"   Total MP3 files: {len(mp3_files)}")
    print(f"   Needed MP3 files: {len(needed_mp3)}")
    print(f"   Excess MP3 files: {len(excess_mp3)}")
    print(f"   Needed slide numbers: {sorted(needed_slide_numbers)}")
    
    if excess_mp3:
        print(f"\n🧹 Excess MP3 files that could be cleaned up:")
        for mp3, slide_num in excess_mp3[:10]:  # Show first 10
            if slide_num:
                print(f"   - {mp3.name} (slide {slide_num})")
            else:
                print(f"   - {mp3.name} (no slide number found)")
        if len(excess_mp3) > 10:
            print(f"   ... and {len(excess_mp3) - 10} more")
    
    return {
        'status': 'analyzed',
        'image_count': len(image_files),
        'total_mp3_count': len(mp3_files),
        'needed_mp3_count': len(needed_mp3),
        'excess_mp3_count': len(excess_mp3),
        'needed_slides': sorted(needed_slide_numbers),
        'excess_files': [mp3.name for mp3, _ in excess_mp3]
    }


def main():
    parser = argparse.ArgumentParser(description='Check MP3 caching behavior')
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
    parser.add_argument('--analyze-matching', action='store_true',
                       help='Analyze which MP3 files match current slides vs. excess files')
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    
    if not base_dir.exists():
        print(f"❌ Base directory does not exist: {base_dir}")
        return
    
    print("🎵 MP3 Caching Analysis Tool")
    print("=" * 50)
    
    if args.all_languages:
        languages = ['en', 'zh-CN', 'yue-HK']
        results = {}
        
        for lang in languages:
            print(f"\n{'='*20} {lang} {'='*20}")
            results[lang] = check_mp3_caching(base_dir, args.presentation, lang)
            
            if args.analyze_matching:
                analyze_file_matching(base_dir, args.presentation, lang)
        
        # Overall summary
        print(f"\n{'='*20} OVERALL SUMMARY {'='*20}")
        total_files = sum(r['total_files'] for r in results.values() if r['status'] == 'found')
        total_size = sum(r['total_size'] for r in results.values() if r['status'] == 'found')
        
        print(f"Total MP3 files across all languages: {total_files}")
        print(f"Total size: {total_size / (1024 * 1024):.2f} MB")
        
        # Check for recent modifications
        recent_langs = []
        for lang, result in results.items():
            if result['status'] == 'found' and result.get('newest_time'):
                current_time = time.time()
                if (current_time - result['newest_time']) < 3600:
                    recent_langs.append(lang)
        
        if recent_langs:
            print(f"⚠️  Languages with recent MP3 modifications: {', '.join(recent_langs)}")
            print("   This might indicate unnecessary regeneration")
        else:
            print("✅ No recent MP3 modifications detected (good caching)")
        
    else:
        result = check_mp3_caching(base_dir, args.presentation, args.language)
        
        if args.analyze_matching:
            analyze_file_matching(base_dir, args.presentation, args.language)


if __name__ == '__main__':
    main()