"""File management service for video synthesis."""

import hashlib
import json
import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import atexit

from core.domain.video_synthesis import VideoSynthesisError

logger = logging.getLogger(__name__)


class VideoFileManager:
    """Manager for temporary files and directories in video synthesis."""
    
    # Class-level registry for cleanup tracking
    _active_managers: Dict[str, 'VideoFileManager'] = {}
    _registry_lock = threading.Lock()
    
    def __init__(self, base_temp_dir: Optional[Path] = None, operation_id: Optional[str] = None, 
                 enable_cache: bool = True, cache_dir: Optional[Path] = None, audio_dir: Optional[Path] = None):
        """
        Initialize video file manager.
        
        Args:
            base_temp_dir: Base directory for temporary files
            operation_id: Unique identifier for this operation
            enable_cache: Whether to enable segment caching for speed
            cache_dir: Directory for persistent cache (if None, derives from audio_dir)
            audio_dir: Audio directory to derive cache location (used if cache_dir is None)
        """
        self.operation_id = operation_id or str(uuid.uuid4())
        self.base_temp_dir = base_temp_dir or Path(tempfile.gettempdir())
        self.enable_cache = enable_cache
        
        # Set up cache directory - prefer audio_dir parent for presentation-specific caching
        if cache_dir:
            self.cache_dir = cache_dir
        elif audio_dir:
            # Save segments next to speech files: <output_dir>/<presentation>_<lang>_segments/
            # Extract parent and add _segments suffix to speech directory name
            speech_parent = audio_dir.parent
            speech_dirname = audio_dir.name
            if speech_dirname.endswith('_speech'):
                segments_dirname = speech_dirname.replace('_speech', '_segments')
            else:
                segments_dirname = f"{speech_dirname}_segments"
            self.cache_dir = speech_parent / segments_dirname
        else:
            # Fallback to temp location (not persistent)
            self.cache_dir = Path(tempfile.gettempdir()) / "video_segments_temp"
        
        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache enabled at: {self.cache_dir}")
        
        # Create unique temporary directory for this operation
        self.temp_dir = self.base_temp_dir / f"video_synthesis_{self.operation_id}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Track created files and directories for cleanup
        self.created_files: List[Path] = []
        self.created_dirs: List[Path] = [self.temp_dir]
        self.cleanup_completed = False
        
        # Cache metadata
        self.cache_metadata_file = self.cache_dir / "cache_metadata.json" if self.enable_cache else None
        
        # Register this manager for cleanup
        with VideoFileManager._registry_lock:
            VideoFileManager._active_managers[self.operation_id] = self
        
        logger.debug(f"Created VideoFileManager with temp dir: {self.temp_dir}")
    
    def get_temp_file_path(self, filename: str, subdirectory: Optional[str] = None) -> Path:
        """
        Get path for a temporary file.
        
        Args:
            filename: Name of the temporary file
            subdirectory: Optional subdirectory within temp dir
            
        Returns:
            Path to temporary file
        """
        if subdirectory:
            subdir_path = self.temp_dir / subdirectory
            subdir_path.mkdir(parents=True, exist_ok=True)
            if subdir_path not in self.created_dirs:
                self.created_dirs.append(subdir_path)
            file_path = subdir_path / filename
        else:
            file_path = self.temp_dir / filename
        
        # Track file for cleanup
        if file_path not in self.created_files:
            self.created_files.append(file_path)
        
        return file_path
    
    def create_segment_temp_dir(self) -> Path:
        """
        Create temporary directory for video segments.
        
        Returns:
            Path to segments directory
        """
        segments_dir = self.temp_dir / "segments"
        segments_dir.mkdir(parents=True, exist_ok=True)
        
        if segments_dir not in self.created_dirs:
            self.created_dirs.append(segments_dir)
        
        logger.debug(f"Created segments directory: {segments_dir}")
        return segments_dir
    
    def create_working_temp_dir(self, purpose: str) -> Path:
        """
        Create temporary directory for specific purpose.
        
        Args:
            purpose: Description of directory purpose (e.g., "processing", "output")
            
        Returns:
            Path to created directory
        """
        working_dir = self.temp_dir / purpose
        working_dir.mkdir(parents=True, exist_ok=True)
        
        if working_dir not in self.created_dirs:
            self.created_dirs.append(working_dir)
        
        logger.debug(f"Created working directory for {purpose}: {working_dir}")
        return working_dir
    
    def generate_segment_cache_key(self, image_path: Path, audio_path: Path, 
                                 video_config: Dict[str, Any], slide_index: Optional[int] = None) -> str:
        """
        Generate cache key for a video segment based on inputs and config.
        
        Args:
            image_path: Path to slide image
            audio_path: Path to audio file
            video_config: Video configuration dictionary
            slide_index: Optional slide index to include in key for uniqueness
            
        Returns:
            Cache key string (includes slide index if provided)
        """
        # Create hash from file contents and config
        hasher = hashlib.sha256()
        
        # Add slide index if provided (ensures unique keys per slide)
        if slide_index is not None:
            hasher.update(f"slide_{slide_index}".encode())
        
        # Add image file hash
        if image_path.exists():
            hasher.update(image_path.read_bytes())
        else:
            hasher.update(str(image_path).encode())
        
        # Add audio file hash
        if audio_path.exists():
            hasher.update(audio_path.read_bytes())
        else:
            hasher.update(str(audio_path).encode())
        
        # Add config hash
        config_str = json.dumps(video_config, sort_keys=True)
        hasher.update(config_str.encode())
        
        cache_key = hasher.hexdigest()[:8]  # Use first 8 chars for readability
        if slide_index is not None:
            cache_key = f"{slide_index}_{cache_key}"
        logger.debug(f"Generated cache key {cache_key} for {image_path.name} + {audio_path.name}")
        return cache_key
    
    def get_cached_segment(self, cache_key: str, output_format: str = "mp4") -> Optional[Path]:
        """
        Get cached video segment if it exists.
        
        Args:
            cache_key: Cache key for the segment
            output_format: Video output format
            
        Returns:
            Path to cached segment or None if not found
        """
        if not self.enable_cache:
            return None
        
        cached_file = self.cache_dir / f"slide_{cache_key}.{output_format}"
        
        if cached_file.exists():
            logger.debug(f"Found cached segment: {cached_file}")
            return cached_file
        
        return None
    
    def cache_segment(self, segment_path: Path, cache_key: str) -> Path:
        """
        Cache a video segment for future use.
        
        Args:
            segment_path: Path to the segment to cache
            cache_key: Cache key for the segment
            
        Returns:
            Path to cached segment
        """
        if not self.enable_cache:
            return segment_path
        
        cached_file = self.cache_dir / f"slide_{cache_key}.{segment_path.suffix[1:]}"
        
        try:
            # Copy segment to cache
            shutil.copy2(segment_path, cached_file)
            
            # Update cache metadata
            self._update_cache_metadata(cache_key, cached_file)
            
            logger.debug(f"Cached segment: {cached_file}")
            return cached_file
            
        except Exception as e:
            logger.warning(f"Failed to cache segment {cache_key}: {e}")
            return segment_path
    
    def _update_cache_metadata(self, cache_key: str, cached_file: Path) -> None:
        """
        Update cache metadata with new entry.
        
        Args:
            cache_key: Cache key
            cached_file: Path to cached file
        """
        if not self.cache_metadata_file:
            return
        
        try:
            # Load existing metadata
            metadata = {}
            if self.cache_metadata_file.exists():
                with open(self.cache_metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Add new entry
            metadata[cache_key] = {
                'file_path': str(cached_file),
                'file_size': cached_file.stat().st_size,
                'created_time': cached_file.stat().st_ctime,
                'last_accessed': cached_file.stat().st_atime
            }
            
            # Save updated metadata
            with open(self.cache_metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to update cache metadata: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enable_cache or not self.cache_dir.exists():
            return {'cache_enabled': False}
        
        try:
            cached_files = list(self.cache_dir.glob("slide_*.mp4")) + list(self.cache_dir.glob("slide_*.webm"))
            total_size = sum(f.stat().st_size for f in cached_files if f.exists())
            
            return {
                'cache_enabled': True,
                'cache_dir': str(self.cache_dir),
                'cached_segments': len(cached_files),
                'total_cache_size_bytes': total_size,
                'total_cache_size_mb': total_size / (1024 * 1024)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {'cache_enabled': True, 'error': str(e)}
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Clear cached segments.
        
        Args:
            older_than_days: Only clear files older than this many days (None = clear all)
            
        Returns:
            Dictionary with cleanup statistics
        """
        if not self.enable_cache or not self.cache_dir.exists():
            return {'cache_enabled': False}
        
        import time
        
        stats = {
            'files_removed': 0,
            'size_freed_bytes': 0,
            'errors': []
        }
        
        try:
            current_time = time.time()
            cutoff_time = current_time - (older_than_days * 24 * 3600) if older_than_days else 0
            
            cached_files = list(self.cache_dir.glob("slide_*"))
            
            for cached_file in cached_files:
                try:
                    if cached_file.stat().st_mtime > cutoff_time and older_than_days:
                        continue  # Skip newer files
                    
                    file_size = cached_file.stat().st_size
                    cached_file.unlink()
                    stats['files_removed'] += 1
                    stats['size_freed_bytes'] += file_size
                    
                except Exception as e:
                    stats['errors'].append(f"Failed to remove {cached_file}: {e}")
            
            # Clear metadata file if clearing all
            if not older_than_days and self.cache_metadata_file and self.cache_metadata_file.exists():
                self.cache_metadata_file.unlink()
            
            logger.info(f"Cache cleanup: {stats['files_removed']} files removed, "
                       f"{stats['size_freed_bytes'] / (1024*1024):.2f} MB freed")
            
            return stats
            
        except Exception as e:
            stats['errors'].append(f"Cache cleanup error: {e}")
            return stats
    
    def ensure_output_directory(self, output_path: Path) -> None:
        """
        Ensure output directory exists and is writable.
        
        Args:
            output_path: Path to output file
            
        Raises:
            VideoSynthesisError: If directory cannot be created or is not writable
        """
        try:
            output_dir = output_path.parent
            
            # Create directory if it doesn't exist
            if not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created output directory: {output_dir}")
            
            # Check if directory is writable
            if not os.access(output_dir, os.W_OK):
                raise VideoSynthesisError(f"Output directory is not writable: {output_dir}")
            
        except Exception as e:
            error_msg = f"Failed to ensure output directory for {output_path}: {e}"
            logger.error(error_msg)
            raise VideoSynthesisError(error_msg) from e
    
    def copy_to_output(self, source_path: Path, output_path: Path) -> Path:
        """
        Copy file from temporary location to final output location.
        
        Args:
            source_path: Source file path
            output_path: Destination file path
            
        Returns:
            Path to copied file
            
        Raises:
            VideoSynthesisError: If copy operation fails
        """
        try:
            logger.debug(f"Copying {source_path} to {output_path}")
            
            # Ensure output directory exists
            self.ensure_output_directory(output_path)
            
            # Copy file
            shutil.copy2(source_path, output_path)
            
            # Verify copy was successful
            if not output_path.exists():
                raise VideoSynthesisError(f"Failed to copy file to {output_path}")
            
            logger.debug(f"Successfully copied file to {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Failed to copy {source_path} to {output_path}: {e}"
            logger.error(error_msg)
            raise VideoSynthesisError(error_msg) from e
    
    def move_to_output(self, source_path: Path, output_path: Path) -> Path:
        """
        Move file from temporary location to final output location.
        
        Args:
            source_path: Source file path
            output_path: Destination file path
            
        Returns:
            Path to moved file
            
        Raises:
            VideoSynthesisError: If move operation fails
        """
        try:
            logger.debug(f"Moving {source_path} to {output_path}")
            
            # Ensure output directory exists
            self.ensure_output_directory(output_path)
            
            # Move file
            shutil.move(str(source_path), str(output_path))
            
            # Remove from tracking since it's no longer temporary
            if source_path in self.created_files:
                self.created_files.remove(source_path)
            
            # Verify move was successful
            if not output_path.exists():
                raise VideoSynthesisError(f"Failed to move file to {output_path}")
            
            logger.debug(f"Successfully moved file to {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"Failed to move {source_path} to {output_path}: {e}"
            logger.error(error_msg)
            raise VideoSynthesisError(error_msg) from e
    
    def get_disk_usage(self) -> Dict[str, int]:
        """
        Get disk usage information for temporary directory.
        
        Returns:
            Dictionary with disk usage statistics
        """
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.created_files:
                if file_path.exists():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            # Get available disk space
            statvfs = os.statvfs(self.temp_dir)
            available_space = statvfs.f_frsize * statvfs.f_bavail
            
            return {
                'temp_files_size_bytes': total_size,
                'temp_files_count': file_count,
                'available_space_bytes': available_space,
                'temp_dir_path': str(self.temp_dir)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get disk usage: {e}")
            return {
                'temp_files_size_bytes': 0,
                'temp_files_count': 0,
                'available_space_bytes': 0,
                'temp_dir_path': str(self.temp_dir)
            }
    
    def cleanup(self, force: bool = False) -> Dict[str, Any]:
        """
        Clean up temporary files and directories.
        
        Args:
            force: If True, ignore errors and continue cleanup
            
        Returns:
            Dictionary with cleanup statistics
        """
        if self.cleanup_completed:
            logger.debug(f"Cleanup already completed for operation {self.operation_id}")
            return {'already_cleaned': True}
        
        logger.info(f"Starting cleanup for operation {self.operation_id}")
        
        cleanup_stats = {
            'files_removed': 0,
            'dirs_removed': 0,
            'errors': [],
            'total_size_freed': 0
        }
        
        try:
            # Calculate total size before cleanup
            initial_size = sum(
                f.stat().st_size for f in self.created_files 
                if f.exists()
            )
            
            # Remove individual files first
            for file_path in self.created_files[:]:  # Copy list to avoid modification during iteration
                try:
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleanup_stats['files_removed'] += 1
                        cleanup_stats['total_size_freed'] += file_size
                        logger.debug(f"Removed file: {file_path}")
                except Exception as e:
                    error_msg = f"Failed to remove file {file_path}: {e}"
                    cleanup_stats['errors'].append(error_msg)
                    if not force:
                        logger.error(error_msg)
                    else:
                        logger.warning(error_msg)
            
            # Remove directories (in reverse order to handle nested dirs)
            for dir_path in reversed(self.created_dirs):
                try:
                    if dir_path.exists() and dir_path != self.base_temp_dir:
                        # Only remove if empty or force is True
                        if force or not any(dir_path.iterdir()):
                            if force:
                                shutil.rmtree(dir_path, ignore_errors=True)
                            else:
                                dir_path.rmdir()
                            cleanup_stats['dirs_removed'] += 1
                            logger.debug(f"Removed directory: {dir_path}")
                except Exception as e:
                    error_msg = f"Failed to remove directory {dir_path}: {e}"
                    cleanup_stats['errors'].append(error_msg)
                    if not force:
                        logger.error(error_msg)
                    else:
                        logger.warning(error_msg)
            
            # Mark cleanup as completed
            self.cleanup_completed = True
            
            # Unregister from active managers
            with VideoFileManager._registry_lock:
                VideoFileManager._active_managers.pop(self.operation_id, None)
            
            logger.info(f"Cleanup completed for operation {self.operation_id}: "
                       f"{cleanup_stats['files_removed']} files, "
                       f"{cleanup_stats['dirs_removed']} directories removed, "
                       f"{cleanup_stats['total_size_freed']} bytes freed")
            
            return cleanup_stats
            
        except Exception as e:
            error_msg = f"Unexpected error during cleanup: {e}"
            cleanup_stats['errors'].append(error_msg)
            logger.error(error_msg)
            return cleanup_stats
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.cleanup(force=True)
    
    def __del__(self):
        """Destructor with cleanup."""
        if not self.cleanup_completed:
            self.cleanup(force=True)
    
    @classmethod
    def cleanup_all_active(cls) -> Dict[str, Any]:
        """
        Clean up all active file managers.
        
        Returns:
            Dictionary with cleanup statistics for all managers
        """
        logger.info("Cleaning up all active VideoFileManager instances")
        
        total_stats = {
            'managers_cleaned': 0,
            'total_files_removed': 0,
            'total_dirs_removed': 0,
            'total_errors': 0,
            'total_size_freed': 0
        }
        
        with cls._registry_lock:
            active_managers = list(cls._active_managers.values())
        
        for manager in active_managers:
            try:
                stats = manager.cleanup(force=True)
                total_stats['managers_cleaned'] += 1
                total_stats['total_files_removed'] += stats.get('files_removed', 0)
                total_stats['total_dirs_removed'] += stats.get('dirs_removed', 0)
                total_stats['total_errors'] += len(stats.get('errors', []))
                total_stats['total_size_freed'] += stats.get('total_size_freed', 0)
            except Exception as e:
                logger.error(f"Failed to cleanup manager {manager.operation_id}: {e}")
                total_stats['total_errors'] += 1
        
        logger.info(f"Cleaned up {total_stats['managers_cleaned']} file managers")
        return total_stats


# Register cleanup function to run at program exit
def _cleanup_at_exit():
    """Cleanup function to run at program exit."""
    try:
        VideoFileManager.cleanup_all_active()
    except Exception as e:
        logger.error(f"Error during exit cleanup: {e}")


atexit.register(_cleanup_at_exit)


class ConcurrentFileManager:
    """Manager for handling concurrent video synthesis operations."""
    
    def __init__(self, base_temp_dir: Optional[Path] = None):
        """
        Initialize concurrent file manager.
        
        Args:
            base_temp_dir: Base directory for temporary files
        """
        self.base_temp_dir = base_temp_dir or Path(tempfile.gettempdir())
        self.operation_managers: Dict[str, VideoFileManager] = {}
        self.lock = threading.Lock()
    
    def create_operation_manager(self, operation_id: Optional[str] = None) -> VideoFileManager:
        """
        Create a new file manager for a video synthesis operation.
        
        Args:
            operation_id: Optional operation identifier
            
        Returns:
            VideoFileManager instance for the operation
        """
        with self.lock:
            manager = VideoFileManager(self.base_temp_dir, operation_id)
            self.operation_managers[manager.operation_id] = manager
            logger.debug(f"Created operation manager: {manager.operation_id}")
            return manager
    
    def get_operation_manager(self, operation_id: str) -> Optional[VideoFileManager]:
        """
        Get existing operation manager by ID.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            VideoFileManager instance or None if not found
        """
        with self.lock:
            return self.operation_managers.get(operation_id)
    
    def cleanup_operation(self, operation_id: str) -> Dict[str, Any]:
        """
        Clean up specific operation.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Cleanup statistics
        """
        with self.lock:
            manager = self.operation_managers.pop(operation_id, None)
            if manager:
                return manager.cleanup()
            else:
                logger.warning(f"No operation manager found for ID: {operation_id}")
                return {'error': 'Operation not found'}
    
    def cleanup_all_operations(self) -> Dict[str, Any]:
        """
        Clean up all operations.
        
        Returns:
            Combined cleanup statistics
        """
        with self.lock:
            managers = list(self.operation_managers.values())
            self.operation_managers.clear()
        
        total_stats = {
            'operations_cleaned': 0,
            'total_files_removed': 0,
            'total_dirs_removed': 0,
            'total_errors': 0,
            'total_size_freed': 0
        }
        
        for manager in managers:
            try:
                stats = manager.cleanup()
                total_stats['operations_cleaned'] += 1
                total_stats['total_files_removed'] += stats.get('files_removed', 0)
                total_stats['total_dirs_removed'] += stats.get('dirs_removed', 0)
                total_stats['total_errors'] += len(stats.get('errors', []))
                total_stats['total_size_freed'] += stats.get('total_size_freed', 0)
            except Exception as e:
                logger.error(f"Failed to cleanup operation {manager.operation_id}: {e}")
                total_stats['total_errors'] += 1
        
        return total_stats
    
    def get_all_operations_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all active operations.
        
        Returns:
            Dictionary mapping operation IDs to their status
        """
        with self.lock:
            status = {}
            for op_id, manager in self.operation_managers.items():
                try:
                    disk_usage = manager.get_disk_usage()
                    status[op_id] = {
                        'temp_dir': str(manager.temp_dir),
                        'files_count': disk_usage['temp_files_count'],
                        'size_bytes': disk_usage['temp_files_size_bytes'],
                        'cleanup_completed': manager.cleanup_completed
                    }
                except Exception as e:
                    status[op_id] = {'error': str(e)}
            
            return status