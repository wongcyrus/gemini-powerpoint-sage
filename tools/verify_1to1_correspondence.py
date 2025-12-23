#!/usr/bin/env python3
"""
Verify 1:1:1 correspondence between images, MP3s, and segments.
This tool checks that slide numbers match across all three file types.
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_slide_number(filename: str) -> int:
    """Extract slide number from filename."""
    match = re.search(r'slide_(\d+)', filename)
    if match:
        return int(match.group(1))
    raise ValueError(f"Cannot extract slide number from: {filename}")


def analyze_files(base_dir: Path, presentation_name: str, language: str) -> Dict:
    """Analyze files for 1:1:1 correspondence."""
    print(f"🔍 Analyzing 1:1:1 correspondence for: {presentation_name} ({language})")
    
    # Directory paths
    visuals_dir = base_dir / f"{presentation_name}_{language}_visuals"
    speech_dir = base_dir / f"{presentation_name}_{language}_speech"
    segments_dir = base_dir / f"{presentation_name}_{language}_segments"
    
    print(f"📁 Visuals: {visuals_dir}")
    print(f"📁 Speech: {speech_dir}")
    print(f"📁 Segments: {segments_dir}")
    
    # Collect files
    image_files = []
    if visuals_dir.exists():
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            image_files.extend(visuals_dir.glob(ext))
    
    mp3_files = []
    if speech_dir.exists():
        mp3_files = list(speech_dir.glob("*.mp3"))
    
    segment_files = []
    if segments_dir.exists():
        for ext in ['*.mp4', '*.webm']:
            segment_files.extend(segments_dir.glob(ext))
    
    print(f"\n📊 File counts:")
    print(f"   Images: {len(image_files)}")
    print(f"   MP3s: {len(mp3_files)}")
    print(f"   Segments: {len(segment_files)}")
    
    # Extract slide numbers
    image_slides = {}
    mp3_slides = {}
    segment_slides = {}
    
    # Process images
    for img in image_files:
        try:
            slide_num = extract_slide_number(img.name)
            image_slides[slide_num] = img
        except ValueError as e:
            print(f"⚠️  Image: {e}")
    
    # Process MP3s
    for mp3 in mp3_files:
        try:
            slide_num = extract_slide_number(mp3.name)
            mp3_slides[slide_num] = mp3
        except ValueError as e:
            print(f"⚠️  MP3: {e}")
    
    # Process segments
    for segment in segment_files:
        try:
            slide_num = extract_slide_number(segment.name)
            segment_slides[slide_num] = segment
        except ValueError as e:
            print(f"⚠️  Segment: {e}")
    
    # Get all slide numbers
    all_slides = set(image_slides.keys()) | set(mp3_slides.keys()) | set(segment_slides.keys())
    
    print(f"\n🎯 Slide numbers found: {sorted(all_slides)}")
    
    # Check correspondence
    perfect_matches = []
    missing_images = []
    missing_mp3s = []
    missing_segments = []
    
    for slide_num in sorted(all_slides):
        has_image = slide_num in image_slides
        has_mp3 = slide_num in mp3_slides
        has_segment = slide_num in segment_slides
        
        if has_image and has_mp3 and has_segment:
            perfect_matches.append(slide_num)
        else:
            if not has_image:
                missing_images.append(slide_num)
            if not has_mp3:
                missing_mp3s.append(slide_num)
            if not has_segment:
                missing_segments.append(slide_num)
    
    print(f"\n✅ Perfect 1:1:1 matches: {len(perfect_matches)} slides")
    if perfect_matches:
        print(f"   Slides: {perfect_matches}")
    
    if missing_images:
        print(f"\n❌ Missing images for slides: {missing_images}")
    
    if missing_mp3s:
        print(f"\n❌ Missing MP3s for slides: {missing_mp3s}")
    
    if missing_segments:
        print(f"\n❌ Missing segments for slides: {missing_segments}")
    
    # Detailed analysis for first few slides
    print(f"\n📋 Detailed analysis (first 5 slides):")
    for slide_num in sorted(all_slides)[:5]:
        img_name = image_slides[slide_num].name if slide_num in image_slides else "MISSING"
        mp3_name = mp3_slides[slide_num].name if slide_num in mp3_slides else "MISSING"
        seg_name = segment_slides[slide_num].name if slide_num in segment_slides else "MISSING"
        
        status = "✅" if slide_num in perfect_matches else "❌"
        print(f"   Slide {slide_num:2d}: {status}")
        print(f"      Image:   {img_name}")
        print(f"      MP3:     {mp3_name}")
        print(f"      Segment: {seg_name}")
    
    if len(all_slides) > 5:
        print(f"   ... and {len(all_slides) - 5} more slides")
    
    # Summary
    total_slides = len(all_slides)
    correspondence_rate = len(perfect_matches) / total_slides * 100 if total_slides > 0 else 0
    
    print(f"\n📈 Summary:")
    print(f"   Total slides: {total_slides}")
    print(f"   Perfect matches: {len(perfect_matches)}")
    print(f"   Correspondence rate: {correspondence_rate:.1f}%")
    
    if correspondence_rate == 100:
        print(f"   🎉 Perfect 1:1:1 correspondence achieved!")
    else:
        print(f"   ⚠️  Correspondence issues detected")
    
    return {
        'total_slides': total_slides,
        'perfect_matches': len(perfect_matches),
        'correspondence_rate': correspondence_rate,
        'missing_images': missing_images,
        'missing_mp3s': missing_mp3s,
        'missing_segments': missing_segments,
        'image_slides': image_slides,
        'mp3_slides': mp3_slides,
        'segment_slides': segment_slides
    }


def main():
    parser = argparse.ArgumentParser(description='Verify 1:1:1 correspondence between images, MP3s, and segments')
    parser.add_argument('--base-dir', 
                       default='/mnt/hgfs/VM Share/ite3001/hkcomic/generate',
                       help='Base directory for files')
    parser.add_argument('--presentation', 
                       default='Introduction to Programming Lecture',
                       help='Presentation name')
    parser.add_argument('--language', 
                       default='zh-CN',
                       help='Language code')
    parser.add_argument('--all-languages', action='store_true',
                       help='Check all common languages')
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    
    if not base_dir.exists():
        print(f"❌ Base directory does not exist: {base_dir}")
        return
    
    print("🔍 1:1:1 Correspondence Verification Tool")
    print("=" * 50)
    
    if args.all_languages:
        languages = ['en', 'zh-CN', 'yue-HK']
        results = {}
        
        for lang in languages:
            print(f"\n{'='*20} {lang} {'='*20}")
            results[lang] = analyze_files(base_dir, args.presentation, lang)
        
        # Overall summary
        print(f"\n{'='*20} OVERALL SUMMARY {'='*20}")
        total_perfect = sum(r['perfect_matches'] for r in results.values())
        total_slides = sum(r['total_slides'] for r in results.values())
        overall_rate = total_perfect / total_slides * 100 if total_slides > 0 else 0
        
        print(f"Total slides across all languages: {total_slides}")
        print(f"Total perfect matches: {total_perfect}")
        print(f"Overall correspondence rate: {overall_rate:.1f}%")
        
        # Show languages with issues
        problem_langs = []
        for lang, result in results.items():
            if result['correspondence_rate'] < 100:
                problem_langs.append(lang)
        
        if problem_langs:
            print(f"⚠️  Languages with correspondence issues: {', '.join(problem_langs)}")
        else:
            print(f"🎉 Perfect 1:1:1 correspondence across all languages!")
        
    else:
        analyze_files(base_dir, args.presentation, args.language)


if __name__ == '__main__':
    main()