#!/usr/bin/env python3
"""
Check which videos already exist to avoid reprocessing.
"""

import argparse
from pathlib import Path
import yaml


def load_config(config_file):
    """Load configuration from YAML file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def check_existing_videos(base_dir, presentation_name, languages):
    """Check which videos already exist."""
    base_path = Path(base_dir)
    
    print(f"🔍 Checking existing videos for: {presentation_name}")
    print(f"📁 Base directory: {base_path}")
    print(f"🌐 Languages: {', '.join(languages)}")
    print()
    
    existing_videos = []
    missing_videos = []
    
    for lang in languages:
        # Generate expected video filename
        safe_name = presentation_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        video_filename = f"{safe_name}_{lang}.mp4"
        video_path = base_path / video_filename
        
        if video_path.exists():
            file_size = video_path.stat().st_size / (1024 * 1024 * 1024)  # GB
            existing_videos.append((lang, video_path, file_size))
            print(f"✅ {lang}: {video_filename} ({file_size:.2f} GB)")
        else:
            missing_videos.append((lang, video_path))
            print(f"❌ {lang}: {video_filename} (missing)")
    
    print()
    print(f"📊 Summary:")
    print(f"   ✅ Existing: {len(existing_videos)}")
    print(f"   ❌ Missing: {len(missing_videos)}")
    
    if existing_videos:
        total_size = sum(size for _, _, size in existing_videos)
        print(f"   💾 Total size: {total_size:.2f} GB")
    
    return existing_videos, missing_videos


def main():
    parser = argparse.ArgumentParser(description='Check existing videos')
    parser.add_argument('--config', default='styles/config.hkcomic.yaml',
                       help='Configuration file')
    parser.add_argument('--base-dir', 
                       default='/mnt/hgfs/VM Share/ite3001/hkcomic/generate',
                       help='Base directory for videos')
    parser.add_argument('--presentation', 
                       default='Introduction to Programming Lecture',
                       help='Presentation name')
    
    args = parser.parse_args()
    
    # Load config to get languages
    try:
        config = load_config(args.config)
        languages = config.get('languages', ['en'])
    except Exception as e:
        print(f"⚠️  Could not load config {args.config}: {e}")
        languages = ['en', 'zh-CN', 'yue-HK']  # Default languages
    
    existing, missing = check_existing_videos(args.base_dir, args.presentation, languages)
    
    if missing:
        print(f"\n🚀 To process missing videos:")
        for lang, video_path in missing:
            print(f"   Process {lang}: {video_path.name}")
    else:
        print(f"\n🎉 All videos exist! No processing needed.")


if __name__ == '__main__':
    main()