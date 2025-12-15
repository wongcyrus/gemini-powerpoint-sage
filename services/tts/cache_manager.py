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
    """Manages TTS audio file caching with content and style-aware hashing."""
    
    def __init__(self, cache_config: TTSCacheConfig):
        """Initialize cache manager with configuration."""
        self.config = cache_config
        self.cache_dir = Path(cache_config.cache_directory)
        self.metadata_file = self.cache_dir / cache_config.metadata_file
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing metadata
        self._metadata = self._load_metadata()
    
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
    
    async def get_cached_audio(self, cache_key: str) -> Optional[TTSResult]:
        """
        Retrieve cached audio if available and not expired.
        
        Args:
            cache_key: Cache key for the audio
            
        Returns:
            TTSResult if cached and valid, None otherwise
        """
        if not self.config.enabled:
            return None
        
        try:
            # Check if cache entry exists in metadata
            if cache_key not in self._metadata:
                return None
            
            entry = self._metadata[cache_key]
            
            # Check if entry is expired
            if self._is_expired(entry):
                await self._remove_cache_entry(cache_key)
                return None
            
            # Check if file exists
            file_path = Path(entry["file_path"])
            if not file_path.exists():
                await self._remove_cache_entry(cache_key)
                return None
            
            # Return TTSResult from cached data
            return TTSResult.from_dict(entry["tts_result"])
            
        except Exception as e:
            logger.warning(f"Error retrieving cached audio for key {cache_key}: {e}")
            return None
    
    async def store_audio(
        self,
        cache_key: str,
        tts_result: TTSResult
    ) -> None:
        """
        Store generated audio in cache.
        
        Args:
            cache_key: Cache key for the audio
            tts_result: TTS result to cache
        """
        if not self.config.enabled:
            return
        
        try:
            # Create cache entry
            entry = {
                "cache_key": cache_key,
                "created_at": datetime.now().isoformat(),
                "file_path": tts_result.file_path,
                "tts_result": tts_result.to_dict()
            }
            
            # Store in metadata
            self._metadata[cache_key] = entry
            
            # Save metadata to disk
            await self._save_metadata()
            
            logger.debug(f"Cached audio with key: {cache_key}")
            
        except Exception as e:
            logger.error(f"Error storing audio in cache: {e}")
            raise TTSCacheError(f"Failed to store audio in cache: {e}")
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if self.config.ttl_hours <= 0:
            return False  # No expiration
        
        try:
            created_at = datetime.fromisoformat(entry["created_at"])
            expiry_time = created_at + timedelta(hours=self.config.ttl_hours)
            return datetime.now() > expiry_time
        except Exception:
            return True  # Treat invalid timestamps as expired
    
    async def _remove_cache_entry(self, cache_key: str) -> None:
        """Remove cache entry and associated file."""
        try:
            if cache_key in self._metadata:
                entry = self._metadata[cache_key]
                
                # Remove file if it exists
                file_path = Path(entry.get("file_path", ""))
                if file_path.exists():
                    file_path.unlink()
                
                # Remove from metadata
                del self._metadata[cache_key]
                
                # Save updated metadata
                await self._save_metadata()
                
        except Exception as e:
            logger.warning(f"Error removing cache entry {cache_key}: {e}")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from disk."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading cache metadata: {e}")
        
        return {}
    
    async def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache metadata: {e}")
            raise TTSCacheError(f"Failed to save cache metadata: {e}")
    
    async def cleanup_expired_entries(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries cleaned up
        """
        if not self.config.enabled:
            return 0
        
        expired_keys = []
        
        for cache_key, entry in self._metadata.items():
            if self._is_expired(entry):
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            await self._remove_cache_entry(cache_key)
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._metadata)
        total_size = 0
        
        for entry in self._metadata.values():
            file_path = Path(entry.get("file_path", ""))
            if file_path.exists():
                total_size += file_path.stat().st_size
        
        return {
            "total_entries": total_entries,
            "total_size_mb": total_size / (1024 * 1024),
            "cache_directory": str(self.cache_dir),
            "enabled": self.config.enabled,
            "ttl_hours": self.config.ttl_hours
        }