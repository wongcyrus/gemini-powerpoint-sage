"""TTS cache management."""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from core.domain.tts import TTSResult, StyleContext, VoiceConfig, TTSCacheError
from config.tts_config import TTSCacheConfig

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages TTS audio file caching with file path based approach (like visual content)."""
    
    def __init__(self, cache_config: TTSCacheConfig):
        """Initialize cache manager with configuration."""
        self.config = cache_config
        self.cache_dir = Path(cache_config.cache_directory)
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("TTS CacheManager initialized with file path based caching (like visual content)")
    
    def generate_cache_key(
        self,
        text: str,
        style_context: StyleContext,
        voice_config: VoiceConfig,
        language_code: str
    ) -> str:
        """
        Generate cache key including style parameters.
        
        Args:
            text: Text content to synthesize
            style_context: Style context for TTS
            voice_config: Voice configuration
            language_code: Language code
            
        Returns:
            SHA256 hash as cache key
        """
        # Normalize text content
        normalized_text = self._normalize_text(text)
        
        # Create cache key components
        key_components = {
            "text": normalized_text,
            "language": language_code,
            "tone": style_context.tone,
            "pace": style_context.pace,
            "emphasis_words": sorted(style_context.emphasis_words),
            "emotional_indicators": sorted(style_context.emotional_indicators),
            "presentation_type": style_context.presentation_type.value,
            "voice_name": voice_config.voice_name,
            "gender": voice_config.gender,
            "speaking_rate": voice_config.speaking_rate,
            "pitch": voice_config.pitch,
            "volume_gain_db": voice_config.volume_gain_db
        }
        
        # Create deterministic hash
        key_string = json.dumps(key_components, sort_keys=True)
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text content for consistent hashing."""
        # Remove extra whitespace and normalize line endings
        normalized = ' '.join(text.split())
        return normalized.strip().lower()
    
    async def get_cached_audio(self, cache_key: str, expected_file_path: str) -> Optional[bytes]:
        """
        Retrieve cached audio if file exists (file path based caching like visual content).
        
        Args:
            cache_key: Cache key for the audio (for logging)
            expected_file_path: Expected file path for the audio
            
        Returns:
            Audio bytes if cached file exists, None otherwise
        """
        if not self.config.enabled:
            return None
        
        try:
            file_path = Path(expected_file_path)
            
            # Simple file existence check (like visual content)
            if file_path.exists():
                # Check TTL if configured
                if self.config.ttl_hours > 0:
                    file_age_hours = (datetime.now().timestamp() - file_path.stat().st_mtime) / 3600
                    if file_age_hours > self.config.ttl_hours:
                        logger.debug(f"Cached audio expired (age: {file_age_hours:.1f}h): {expected_file_path}")
                        file_path.unlink()  # Remove expired file
                        return None
                
                # Read and return audio data
                with open(file_path, 'rb') as f:
                    audio_data = f.read()
                
                logger.debug(f"Cache hit for audio file: {expected_file_path}")
                return audio_data
            
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving cached audio from {expected_file_path}: {e}")
            return None
    
    async def store_audio(
        self,
        cache_key: str,
        file_path: str
    ) -> None:
        """
        Store generated audio in cache (file path based - no metadata needed).
        
        Args:
            cache_key: Cache key for the audio (for logging)
            file_path: Path where audio file is stored
        """
        if not self.config.enabled:
            return
        
        # With file path based caching, storage is handled by the storage manager
        # This method is kept for compatibility but doesn't need to do anything
        logger.debug(f"Audio cached at: {file_path} (key: {cache_key[:8]}...)")
    
    def cleanup_expired_files(self, output_directories: list) -> int:
        """
        Clean up expired audio files based on file timestamps.
        
        Args:
            output_directories: List of directories to scan for audio files
            
        Returns:
            Number of files cleaned up
        """
        if not self.config.enabled or self.config.ttl_hours <= 0:
            return 0
        
        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (self.config.ttl_hours * 3600)
        
        try:
            for directory in output_directories:
                dir_path = Path(directory)
                if not dir_path.exists():
                    continue
                
                for audio_file in dir_path.glob("**/*.mp3"):
                    try:
                        if audio_file.stat().st_mtime < cutoff_time:
                            audio_file.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned up expired audio file: {audio_file}")
                    except Exception as e:
                        logger.warning(f"Error cleaning up {audio_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired audio files")
            
        except Exception as e:
            logger.error(f"Error during audio file cleanup: {e}")
        
        return cleaned_count
    
    def get_cache_stats(self, output_directories: list) -> Dict[str, Any]:
        """Get cache statistics by scanning audio files directly."""
        total_files = 0
        total_size = 0
        
        try:
            for directory in output_directories:
                dir_path = Path(directory)
                if not dir_path.exists():
                    continue
                
                for audio_file in dir_path.glob("**/*.mp3"):
                    if audio_file.exists():
                        total_files += 1
                        total_size += audio_file.stat().st_size
        
        except Exception as e:
            logger.warning(f"Error calculating cache stats: {e}")
        
        return {
            "total_files": total_files,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_approach": "file_path_based",
            "enabled": self.config.enabled,
            "ttl_hours": self.config.ttl_hours
        }