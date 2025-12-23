#!/usr/bin/env python3
"""
Clean up excess MP3 files that don't match current slide images.
This simulates the cleanup logic from the CLI.
"""

import argparse
import re
from pathlib import Path
from typing import List, Set, Tuple


def natural_sort_key(path):
    """Natural sorting key for filenames."""
    filename = path.name
    def convert(text):
        return int(text) if text.isdigit() else text.lower()
    return [convert(c) for c in re.split('([0-9]+)', filename)]


def find_needed_slide_numbers(image_files: List[Path]) -> Set[int]:
    """Extract slide numbers from image filenames."""
    needed_slide_numbers = set()
    for img in image_files:
        try:
            match = re.search(r'slide_(\d+)', img.name)
            if match:
                needed_slide_numbers.add(int(match.group(1)))
        except:
            pass
    return needed_slide_numbers


def categorize_mp3_files(mp3_files: List[Path], needed_slide_numbers: Set[int], max_needed: int) -> Tuple[List[Path], List[Path]]:
    """Categorize MP3 files into needed vs. excess."""
    needed_mp3 = []
    excess_mp3 = []
    
    for mp3 in mp3_files:
        try:
            match = re.search(r'slide_(\d+)', mp3.name)
            if match:
                slide_num = int(match.group(1))
                if slide_num in needed_slide_numbers and len(needed_mp3) < max_needed:
                    needed_mp3.append(mp3)
                else:
                    excess_mp3.append(mp3)
            else:
                excess_mp3.append(mp3)
        except:
            excess_mp3.append(mp3)
    
    return needed_mp3, excess_mp3


def cleanup_excess_mp3(base_dir: Path, presentation_name: str, language: str, dry_run: bool = True) -> dict:
    """Clean up excess MP3 files for a presentation."""
    print(f"🧹 Cleaning up excess MP3 files for: {presentation_name} ({language})")
    
    # Find directories
    speech_dir_name = f"{presentation_name}_{language}_speech"
    visuals_dir_name = f"{presentation_name}_{language}_visuals"
    
    speech_dir = base_dir / speech_dir_name
    visuals_dir = base_dir / visuals_dir_name
    
    print(f"📁 Speech directory: {speech_dir}")
    print(f"📁 Visuals directory: {visuals_dir}")
    
    if not speech_dir.exists():
        print("❌ Speech directory does not exist")
        return {'status': 'no_speech_dir'}
    
    if not visuals_dir.exists():
        print("❌ Visuals directory does not exist")
        return {'status': 'no_visuals_dir'}
    
    # Get files
    mp3_files = list(speech_dir.glob("*.mp3"))
    mp3_files = sorted(mp3_files, key=natural_sort_key)
    
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        image_files.extend(visuals_dir.glob(ext))
    image_files = sorted(image_files, key=natural_sort_key)
    
    if not mp3_files:
        print("❌ No MP3 files found")
        return {'status': 'no_mp3_files'}
    
    if not image_files:
        print("❌ No image files found")
        return {'status': 'no_image_files'}
    
    print(f"📊 Found {len(image_files)} image files and {len(mp3_files)} MP3 files")
    
    # Find needed slide numbers
    needed_slide_numbers = find_needed_slide_numbers(image_files)
    print(f"🎯 Need audio for slides: {sorted(needed_slide_numbers)}")
    
    # Categorize MP3 files
    needed_mp3, excess_mp3 = categorize_mp3_files(mp3_files, needed_slide_numbers, len(image_files))
    
    print(f"✅ Needed MP3 files: {len(needed_mp3)}")
    print(f"🗑️  Excess MP3 files: {len(excess_mp3)}")
    
    if not excess_mp3:
        print("✨ No excess files to clean up!")
        return {
            'status': 'clean',
            'needed_count': len(needed_mp3),
            'excess_count': 0,
            'cleaned_count': 0
        }
    
    # Show excess files
    print(f"\n🗑️  Excess MP3 files to {'remove' if not dry_run else 'be removed'}:")
    total_size = 0
    for mp3 in excess_mp3:
        try:
            size = mp3.stat().st_size
            total_size += size
            size_kb = size / 1024
            print(f"   - {mp3.name} ({size_kb:.1f} KB)")
        except:
            print(f"   - {mp3.name} (size unknown)")
    
    print(f"💾 Total size to free: {total_size / (1024 * 1024):.2f} MB")
    
    # Clean up files
    cleaned_count = 0
    errors = 0
    
    if dry_run:
        print(f"\n🔍 DRY RUN - Would remove {len(excess_mp3)} files")
        cleaned_count = len(excess_mp3)
    else:
        print(f"\n🧹 Removing {len(excess_mp3)} excess files...")
        for mp3 in excess_mp3:
            try:
                mp3.unlink()
                print(f"   ✅ Removed: {mp3.name}")
                cleaned_count += 1
            except Exception as e:
                print(f"   ❌ Failed to remove {mp3.name}: {e}")
                errors += 1
    
    return {
        'status': 'cleaned',
        'needed_count': len(needed_mp3),
        'excess_count': len(excess_mp3),
        'cleaned_count': cleaned_count,
        'errors': errors,
        'size_freed': total_size
    }


def main():
    parser = argparse.ArgumentParser(description='Clean up excess MP3 files')
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
                       help='Clean up all common languages')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be cleaned without actually removing files')
    parser.add_argument('--force', action='store_true',
                       help='Actually remove files (overrides dry-run)')
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    
    if not base_dir.exists():
        print(f"❌ Base directory does not exist: {base_dir}")
        return
    
    # Determine if this is a dry run
    dry_run = args.dry_run and not args.force
    
    print("🧹 MP3 Excess File Cleanup Tool")
    print("=" * 50)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be removed")
    else:
        print("⚠️  LIVE MODE - Files will be permanently removed!")
    
    print()
    
    if args.all_languages:
        languages = ['en', 'zh-CN', 'yue-HK']
        total_cleaned = 0
        total_size_freed = 0
        
        for lang in languages:
            print(f"\n{'='*20} {lang} {'='*20}")
            result = cleanup_excess_mp3(base_dir, args.presentation, lang, dry_run)
            
            if result['status'] == 'cleaned':
                total_cleaned += result['cleaned_count']
                total_size_freed += result.get('size_freed', 0)
        
        # Overall summary
        print(f"\n{'='*20} OVERALL SUMMARY {'='*20}")
        action = "Would clean" if dry_run else "Cleaned"
        print(f"{action} {total_cleaned} excess MP3 files")
        print(f"Total size freed: {total_size_freed / (1024 * 1024):.2f} MB")
        
    else:
        result = cleanup_excess_mp3(base_dir, args.presentation, args.language, dry_run)
        
        if result['status'] == 'cleaned':
            action = "Would clean" if dry_run else "Cleaned"
            print(f"\n✅ {action} {result['cleaned_count']} excess files")
            if result.get('errors', 0) > 0:
                print(f"⚠️  {result['errors']} errors occurred")
    
    if dry_run and not args.force:
        print(f"\n💡 To actually remove files, run with --force")


if __name__ == '__main__':
    main()