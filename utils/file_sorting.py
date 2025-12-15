"""Utility functions for file sorting."""

import re
from pathlib import Path
from typing import List, Union


def natural_sort_key(path: Union[Path, str]) -> List[Union[int, str]]:
    """
    Generate sort key for natural sorting that handles numbers correctly.
    
    This ensures that files are sorted in natural order:
    - slide_1.png, slide_2.png, ..., slide_10.png, slide_11.png
    
    Instead of lexicographic order:
    - slide_1.png, slide_10.png, slide_11.png, ..., slide_2.png
    
    Args:
        path: File path (Path object or string)
        
    Returns:
        List of integers and strings for sorting
        
    Example:
        >>> files = [Path("slide_10.png"), Path("slide_2.png"), Path("slide_1.png")]
        >>> sorted(files, key=natural_sort_key)
        [Path("slide_1.png"), Path("slide_2.png"), Path("slide_10.png")]
    """
    if isinstance(path, Path):
        filename = path.name
    else:
        filename = str(path)
    
    def convert(text: str) -> Union[int, str]:
        """Convert text to int if it's a digit, otherwise lowercase string."""
        return int(text) if text.isdigit() else text.lower()
    
    # Split filename into parts, converting numbers to integers
    return [convert(c) for c in re.split('([0-9]+)', filename)]


def natural_sort_files(files: List[Path]) -> List[Path]:
    """
    Sort files using natural sorting.
    
    Args:
        files: List of file paths
        
    Returns:
        Sorted list of file paths
    """
    return sorted(files, key=natural_sort_key)


def pair_slide_audio_files(slide_images: List[Path], audio_files: List[Path]) -> List[tuple[Path, Path]]:
    """
    Pair slide images with audio files using natural sorting.
    
    Args:
        slide_images: List of slide image paths
        audio_files: List of audio file paths
        
    Returns:
        List of (slide_image, audio_file) tuples
        
    Raises:
        ValueError: If the number of slides and audio files don't match
    """
    # Sort both lists using natural sorting
    sorted_slides = natural_sort_files(slide_images)
    sorted_audio = natural_sort_files(audio_files)
    
    if len(sorted_slides) != len(sorted_audio):
        raise ValueError(
            f"Number of slide images ({len(sorted_slides)}) must match "
            f"number of audio files ({len(sorted_audio)})"
        )
    
    return list(zip(sorted_slides, sorted_audio))


def extract_slide_number(filename: str) -> int:
    """
    Extract slide number from filename.
    
    Args:
        filename: Filename like "slide_5_reimagined.png" or "slide_10_abc123.mp3"
        
    Returns:
        Slide number as integer
        
    Raises:
        ValueError: If no slide number found in filename
        
    Example:
        >>> extract_slide_number("slide_5_reimagined.png")
        5
        >>> extract_slide_number("slide_10_abc123.mp3")
        10
    """
    # Look for pattern like "slide_N" where N is a number
    match = re.search(r'slide_(\d+)', filename)
    if match:
        return int(match.group(1))
    
    # Fallback: look for any number in the filename
    numbers = re.findall(r'\d+', filename)
    if numbers:
        return int(numbers[0])
    
    raise ValueError(f"No slide number found in filename: {filename}")


def verify_slide_audio_pairing(slide_images: List[Path], audio_files: List[Path]) -> bool:
    """
    Verify that slide images and audio files are properly paired by slide number.
    
    Args:
        slide_images: List of slide image paths (sorted)
        audio_files: List of audio file paths (sorted)
        
    Returns:
        True if pairing looks correct, False otherwise
    """
    if len(slide_images) != len(audio_files):
        return False
    
    try:
        for slide_path, audio_path in zip(slide_images, audio_files):
            slide_num = extract_slide_number(slide_path.name)
            audio_num = extract_slide_number(audio_path.name)
            
            if slide_num != audio_num:
                print(f"Warning: Slide number mismatch - {slide_path.name} (slide {slide_num}) "
                      f"paired with {audio_path.name} (slide {audio_num})")
                return False
        
        return True
        
    except ValueError as e:
        print(f"Warning: Could not verify pairing - {e}")
        return False


def print_file_pairing_preview(slide_images: List[Path], audio_files: List[Path], max_show: int = 5):
    """
    Print a preview of how files will be paired.
    
    Args:
        slide_images: List of slide image paths (sorted)
        audio_files: List of audio file paths (sorted)
        max_show: Maximum number of pairs to show
    """
    print(f"\nFile pairing preview (first {max_show}):")
    
    for i in range(min(max_show, len(slide_images), len(audio_files))):
        slide_name = slide_images[i].name
        audio_name = audio_files[i].name
        
        # Try to extract and show slide numbers for verification
        try:
            slide_num = extract_slide_number(slide_name)
            audio_num = extract_slide_number(audio_name)
            
            if slide_num == audio_num:
                status = "✓"
            else:
                status = "⚠️"
                
            print(f"  {i+1}: {slide_name} + {audio_name} {status} (slide {slide_num} + {audio_num})")
            
        except ValueError:
            print(f"  {i+1}: {slide_name} + {audio_name}")
    
    if len(slide_images) > max_show:
        print(f"  ... and {len(slide_images) - max_show} more pairs")
    
    # Verify overall pairing
    if verify_slide_audio_pairing(slide_images, audio_files):
        print("✓ File pairing verification passed")
    else:
        print("⚠️  File pairing verification failed - check slide numbers")