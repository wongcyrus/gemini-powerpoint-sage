#!/usr/bin/env python3
"""
Simple disk usage monitor for video synthesis operations.
"""

import os
import time
from pathlib import Path


def get_disk_usage(path):
    """Get disk usage for a path."""
    try:
        statvfs = os.statvfs(path)
        total = statvfs.f_frsize * statvfs.f_blocks
        available = statvfs.f_frsize * statvfs.f_bavail
        used = total - available
        return {
            'total_gb': total / (1024**3),
            'used_gb': used / (1024**3),
            'available_gb': available / (1024**3),
            'used_percent': (used / total) * 100 if total > 0 else 0
        }
    except Exception as e:
        return {'error': str(e)}


def count_temp_files(path):
    """Count temporary video files in a directory."""
    if not Path(path).exists():
        return 0
    
    count = 0
    patterns = ['video_synthesis_*', 'segment_*', 'chunk_*']
    
    for pattern in patterns:
        count += len(list(Path(path).glob(pattern)))
    
    return count


def main():
    paths_to_monitor = ['/tmp', 'output', '.']
    
    print("=== Disk Usage Monitor ===")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for path in paths_to_monitor:
        path_obj = Path(path)
        if path_obj.exists():
            usage = get_disk_usage(path)
            temp_files = count_temp_files(path)
            
            if 'error' not in usage:
                print(f"{path}:")
                print(f"  Used: {usage['used_gb']:.2f} GB ({usage['used_percent']:.1f}%)")
                print(f"  Available: {usage['available_gb']:.2f} GB")
                print(f"  Temp files/dirs: {temp_files}")
                
                # Warning if disk usage is high
                if usage['used_percent'] > 90:
                    print(f"  ⚠️  WARNING: Disk usage is very high!")
                elif usage['used_percent'] > 80:
                    print(f"  ⚠️  CAUTION: Disk usage is getting high")
                
                print()
            else:
                print(f"{path}: Error - {usage['error']}")
    
    print("To clean up temporary files, run:")
    print("  python tools/cleanup_temp_files.py --dry-run")
    print("  python tools/cleanup_temp_files.py  # (to actually remove)")


if __name__ == '__main__':
    main()