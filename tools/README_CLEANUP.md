# Video Synthesis Cleanup Tools

This directory contains utilities to help manage disk space and clean up temporary files created during video synthesis operations.

## Problem Solved

During video synthesis, temporary files are created in `/tmp` and other directories. These files can consume significant disk space (sometimes duplicating the final output size). The tools here help:

1. **Prevent disk space issues** by automatically cleaning up temp files after successful video creation
2. **Monitor disk usage** to warn before running out of space
3. **Manually clean up** orphaned temporary files if automatic cleanup fails

## Tools

### 1. `monitor_disk_usage.py`
Quick disk usage checker that shows current space usage and temporary file counts.

```bash
python tools/monitor_disk_usage.py
```

**Output example:**
```
=== Disk Usage Monitor ===
/tmp:
  Used: 121.49 GB (82.9%)
  Available: 25.09 GB
  Temp files/dirs: 0
  ⚠️  CAUTION: Disk usage is getting high
```

### 2. `cleanup_temp_files.py`
Comprehensive temporary file cleanup utility with dry-run support.

```bash
# See what would be cleaned up (safe)
python tools/cleanup_temp_files.py --dry-run

# Actually remove temporary files
python tools/cleanup_temp_files.py

# Include output directory in scan
python tools/cleanup_temp_files.py --include-output --dry-run

# Only clean files larger than 10MB
python tools/cleanup_temp_files.py --min-size-mb 10
```

**Features:**
- Scans `/tmp` and other directories for video temporary files
- Shows largest files first
- Supports dry-run mode for safety
- Removes empty temporary directories
- Provides detailed statistics

## Automatic Cleanup

The video synthesis service now includes automatic cleanup:

### Configuration (`config/cleanup_config.py`)
- `IMMEDIATE_CLEANUP_AFTER_SUCCESS = True` - Clean up temp files immediately after successful video creation
- `AGGRESSIVE_CLEANUP_ON_ERROR = True` - Force cleanup even if there are errors
- `MIN_FREE_SPACE_GB = 1.0` - Minimum free space before refusing to start
- `WARN_FREE_SPACE_GB = 2.0` - Warn when free space is below this

### How It Works
1. **Before synthesis**: Check available disk space
2. **During synthesis**: Create temporary files as needed
3. **After success**: Immediately clean up all temporary files
4. **After error**: Force cleanup of any remaining temporary files

## Usage Recommendations

### Daily Monitoring
Run the monitor script to check disk usage:
```bash
python tools/monitor_disk_usage.py
```

### Weekly Cleanup
Run the cleanup tool to catch any orphaned files:
```bash
python tools/cleanup_temp_files.py --dry-run
python tools/cleanup_temp_files.py  # if files found
```

### Before Large Operations
Check disk space before processing many videos:
```bash
python tools/monitor_disk_usage.py
```

### Emergency Cleanup
If you run out of disk space:
```bash
# Clean up all video temp files immediately
python tools/cleanup_temp_files.py --min-size-mb 1

# Check what space was freed
python tools/monitor_disk_usage.py
```

## File Patterns Detected

The cleanup tools look for these temporary file patterns:
- `video_synthesis_*` directories
- `segment_*.mp4`, `segment_*.webm` files
- `chunk_*.mp4`, `chunk_*.webm` files
- Files with `temp`, `tmp` in the name
- `concat_*.txt` files

## Safety Features

- **Dry-run mode**: Always test with `--dry-run` first
- **Size thresholds**: Only clean files above minimum size
- **Pattern matching**: Only removes files matching temporary patterns
- **Logging**: Detailed logs of what was cleaned up
- **Error handling**: Continues cleanup even if some files can't be removed

## Troubleshooting

### "Permission denied" errors
Some temporary files may be locked by running processes. Stop any video synthesis operations and try again.

### Files not detected
The cleanup tools look for specific patterns. If you have temporary files with different names, you may need to clean them manually.

### Disk still full after cleanup
Check for other large files in `/tmp`:
```bash
du -h /tmp | sort -hr | head -20
```