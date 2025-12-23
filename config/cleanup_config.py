"""
Configuration for temporary file cleanup behavior.
"""

from pathlib import Path
from typing import Dict, Any


class CleanupConfig:
    """Configuration for temporary file cleanup."""
    
    # Disk space thresholds
    MIN_FREE_SPACE_GB = 1.5  # Minimum free space before refusing to start (increased)
    WARN_FREE_SPACE_GB = 3.0  # Warn when free space is below this (increased)
    
    # Cleanup behavior
    IMMEDIATE_CLEANUP_AFTER_SUCCESS = True  # Clean up temp files immediately after successful video creation
    AGGRESSIVE_CLEANUP_ON_ERROR = True      # Force cleanup even if there are errors
    CLEANUP_EMPTY_DIRS = True               # Remove empty temporary directories
    CHUNKED_PROCESSING_THRESHOLD = 100      # Use chunked processing for presentations with more slides
    CHUNK_SIZE = 50                         # Process this many slides at a time for large presentations
    
    # File size thresholds for cleanup warnings
    LARGE_TEMP_FILE_MB = 100  # Warn about temp files larger than this
    
    # Monitoring
    LOG_DISK_USAGE = True     # Log disk usage during operations
    WARN_HIGH_DISK_USAGE = 80  # Warn when disk usage exceeds this percentage
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get cleanup configuration as dictionary."""
        return {
            'min_free_space_gb': cls.MIN_FREE_SPACE_GB,
            'warn_free_space_gb': cls.WARN_FREE_SPACE_GB,
            'immediate_cleanup_after_success': cls.IMMEDIATE_CLEANUP_AFTER_SUCCESS,
            'aggressive_cleanup_on_error': cls.AGGRESSIVE_CLEANUP_ON_ERROR,
            'cleanup_empty_dirs': cls.CLEANUP_EMPTY_DIRS,
            'large_temp_file_mb': cls.LARGE_TEMP_FILE_MB,
            'log_disk_usage': cls.LOG_DISK_USAGE,
            'warn_high_disk_usage': cls.WARN_HIGH_DISK_USAGE,
            'chunked_processing_threshold': cls.CHUNKED_PROCESSING_THRESHOLD,
            'chunk_size': cls.CHUNK_SIZE
        }
    
    @classmethod
    def should_cleanup_immediately(cls) -> bool:
        """Check if immediate cleanup should be performed."""
        return cls.IMMEDIATE_CLEANUP_AFTER_SUCCESS
    
    @classmethod
    def should_force_cleanup_on_error(cls) -> bool:
        """Check if aggressive cleanup should be performed on errors."""
        return cls.AGGRESSIVE_CLEANUP_ON_ERROR
    
    @classmethod
    def should_use_chunked_processing(cls, slide_count: int) -> bool:
        """Check if chunked processing should be used for large presentations."""
        return slide_count > cls.CHUNKED_PROCESSING_THRESHOLD
    
    @classmethod
    def get_chunk_size(cls) -> int:
        """Get the chunk size for processing large presentations."""
        return cls.CHUNK_SIZE