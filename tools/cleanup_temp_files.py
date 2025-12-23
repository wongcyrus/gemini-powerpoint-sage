#!/usr/bin/env python3
"""
Utility script to clean up temporary video files and monitor disk usage.
Use this to manually clean up temp files if the automatic cleanup fails.
"""

import argparse
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_disk_usage(path: Path) -> Dict[str, int]:
    """Get disk usage statistics for a path."""
    try:
        statvfs = os.statvfs(path)
        total_space = statvfs.f_frsize * statvfs.f_blocks
        available_space = statvfs.f_frsize * statvfs.f_bavail
        used_space = total_space - available_space
        
        return {
            'total_bytes': total_space,
            'used_bytes': used_space,
            'available_bytes': available_space,
            'used_percent': (used_space / total_space) * 100 if total_space > 0 else 0
        }
    except Exception as e:
        logger.error(f"Failed to get disk usage for {path}: {e}")
        return {}


def find_video_temp_files(base_dirs: List[Path]) -> List[Tuple[Path, int]]:
    """Find temporary video files in the specified directories."""
    temp_files = []
    video_patterns = ['*.mp4', '*.avi', '*.mkv', '*.webm', '*.mov']
    temp_patterns = ['video_synthesis_*', 'segment_*', 'chunk_*', 'concat_*']
    
    for base_dir in base_dirs:
        if not base_dir.exists():
            continue
            
        logger.info(f"Scanning {base_dir} for temporary video files...")
        
        # Look for video synthesis temp directories
        for pattern in temp_patterns:
            for item in base_dir.glob(pattern):
                if item.is_dir():
                    # Scan directory for video files
                    for video_pattern in video_patterns:
                        for video_file in item.rglob(video_pattern):
                            if video_file.is_file():
                                try:
                                    size = video_file.stat().st_size
                                    temp_files.append((video_file, size))
                                except Exception as e:
                                    logger.warning(f"Could not get size for {video_file}: {e}")
                elif item.is_file():
                    # Check if it's a video file
                    if any(item.name.endswith(ext[1:]) for ext in video_patterns):
                        try:
                            size = item.stat().st_size
                            temp_files.append((item, size))
                        except Exception as e:
                            logger.warning(f"Could not get size for {item}: {e}")
        
        # Also look for orphaned video files that might be temp files
        for video_pattern in video_patterns:
            for video_file in base_dir.glob(video_pattern):
                if video_file.is_file():
                    # Check if filename suggests it's a temp file
                    name_lower = video_file.name.lower()
                    if any(pattern in name_lower for pattern in ['temp', 'tmp', 'segment', 'chunk']):
                        try:
                            size = video_file.stat().st_size
                            temp_files.append((video_file, size))
                        except Exception as e:
                            logger.warning(f"Could not get size for {video_file}: {e}")
    
    return temp_files


def cleanup_temp_files(temp_files: List[Tuple[Path, int]], dry_run: bool = True) -> Dict[str, int]:
    """Clean up temporary files."""
    stats = {
        'files_removed': 0,
        'size_freed': 0,
        'errors': 0
    }
    
    for file_path, file_size in temp_files:
        try:
            if dry_run:
                logger.info(f"Would remove: {file_path} ({file_size / (1024*1024):.2f} MB)")
                stats['files_removed'] += 1
                stats['size_freed'] += file_size
            else:
                logger.info(f"Removing: {file_path} ({file_size / (1024*1024):.2f} MB)")
                file_path.unlink()
                stats['files_removed'] += 1
                stats['size_freed'] += file_size
                
        except Exception as e:
            logger.error(f"Failed to remove {file_path}: {e}")
            stats['errors'] += 1
    
    return stats


def cleanup_empty_directories(base_dirs: List[Path], dry_run: bool = True) -> int:
    """Clean up empty temporary directories."""
    dirs_removed = 0
    temp_patterns = ['video_synthesis_*', 'segment_*', 'chunk_*']
    
    for base_dir in base_dirs:
        if not base_dir.exists():
            continue
            
        for pattern in temp_patterns:
            for item in base_dir.glob(pattern):
                if item.is_dir():
                    try:
                        # Check if directory is empty
                        if not any(item.iterdir()):
                            if dry_run:
                                logger.info(f"Would remove empty directory: {item}")
                            else:
                                logger.info(f"Removing empty directory: {item}")
                                item.rmdir()
                            dirs_removed += 1
                    except Exception as e:
                        logger.warning(f"Could not remove directory {item}: {e}")
    
    return dirs_removed


def main():
    parser = argparse.ArgumentParser(description='Clean up temporary video files')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be cleaned up without actually removing files')
    parser.add_argument('--temp-dirs', nargs='+', 
                       default=['/tmp', str(Path.home() / 'tmp')],
                       help='Directories to scan for temp files')
    parser.add_argument('--include-output', action='store_true',
                       help='Also scan output directory for temp files')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory to scan if --include-output is used')
    parser.add_argument('--min-size-mb', type=float, default=1.0,
                       help='Minimum file size in MB to consider for cleanup')
    
    args = parser.parse_args()
    
    # Convert string paths to Path objects
    scan_dirs = [Path(d) for d in args.temp_dirs]
    
    if args.include_output:
        output_dir = Path(args.output_dir)
        if output_dir.exists():
            scan_dirs.append(output_dir)
    
    logger.info("=== Video Temporary File Cleanup Utility ===")
    
    # Show disk usage for each directory
    logger.info("\n=== Disk Usage ===")
    for scan_dir in scan_dirs:
        if scan_dir.exists():
            usage = get_disk_usage(scan_dir)
            if usage:
                logger.info(f"{scan_dir}: {usage['used_percent']:.1f}% used "
                           f"({usage['available_bytes'] / (1024**3):.2f} GB available)")
    
    # Find temporary files
    logger.info("\n=== Scanning for Temporary Files ===")
    temp_files = find_video_temp_files(scan_dirs)
    
    # Filter by minimum size
    min_size_bytes = args.min_size_mb * 1024 * 1024
    temp_files = [(path, size) for path, size in temp_files if size >= min_size_bytes]
    
    if not temp_files:
        logger.info("No temporary video files found!")
        return
    
    # Sort by size (largest first)
    temp_files.sort(key=lambda x: x[1], reverse=True)
    
    total_size = sum(size for _, size in temp_files)
    logger.info(f"Found {len(temp_files)} temporary files totaling {total_size / (1024**3):.2f} GB")
    
    # Show top 10 largest files
    logger.info("\n=== Largest Temporary Files ===")
    for i, (file_path, file_size) in enumerate(temp_files[:10]):
        logger.info(f"{i+1:2d}. {file_path} ({file_size / (1024*1024):.2f} MB)")
    
    if len(temp_files) > 10:
        logger.info(f"... and {len(temp_files) - 10} more files")
    
    # Clean up files
    logger.info(f"\n=== {'DRY RUN - ' if args.dry_run else ''}Cleaning Up Files ===")
    cleanup_stats = cleanup_temp_files(temp_files, dry_run=args.dry_run)
    
    # Clean up empty directories
    dirs_removed = cleanup_empty_directories(scan_dirs, dry_run=args.dry_run)
    
    # Summary
    logger.info("\n=== Summary ===")
    action = "Would remove" if args.dry_run else "Removed"
    logger.info(f"{action} {cleanup_stats['files_removed']} files "
               f"({cleanup_stats['size_freed'] / (1024**3):.2f} GB)")
    logger.info(f"{action} {dirs_removed} empty directories")
    
    if cleanup_stats['errors'] > 0:
        logger.warning(f"Encountered {cleanup_stats['errors']} errors during cleanup")
    
    if args.dry_run:
        logger.info("\nTo actually remove these files, run again without --dry-run")


if __name__ == '__main__':
    main()