"""Caching system for prompt rewriter to avoid redundant LLM API calls."""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached prompt entry."""
    cache_key: str
    prompt_type: str
    base_prompt_hash: str
    style_hash: str
    rewritten_prompt: str
    created_at: str
    accessed_at: str


@dataclass
class CacheMetadata:
    """Metadata for cache statistics and management."""
    version: str = "1.0"
    created_at: str = ""
    total_entries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_cleanup: str = ""


class PromptCache:
    """
    File-based caching system for prompt rewriter results.
    
    Provides fast retrieval of previously rewritten prompts to avoid
    expensive LLM API calls when the same prompt/style combination
    is requested multiple times.
    """
    
    def __init__(self, cache_dir: str = None):
        """
        Initialize the prompt cache.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to cache/prompt_rewriter
        """
        # Get cache directory from environment or use default
        self.cache_dir = Path(cache_dir or os.getenv("PROMPT_CACHE_DIR", "cache/prompt_rewriter"))
        self.cache_enabled = os.getenv("PROMPT_CACHE_ENABLED", "true").lower() == "true"
        self.max_size_mb = float(os.getenv("PROMPT_CACHE_MAX_SIZE_MB", "100"))
        self.ttl_days = int(os.getenv("PROMPT_CACHE_TTL_DAYS", "30"))
        
        # Initialize cache directory and metadata
        self._initialize_cache()
        
        logger.info(f"PromptCache initialized: enabled={self.cache_enabled}, dir={self.cache_dir}")
    
    def _initialize_cache(self) -> None:
        """Initialize cache directory and metadata file."""
        try:
            # Create cache directory if it doesn't exist
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize metadata file if it doesn't exist
            metadata_path = self.cache_dir / "cache_metadata.json"
            if not metadata_path.exists():
                metadata = CacheMetadata(
                    created_at=datetime.now().isoformat(),
                    last_cleanup=datetime.now().isoformat()
                )
                self._save_metadata(metadata)
                logger.info(f"Created new cache metadata at {metadata_path}")
            else:
                logger.info(f"Using existing cache at {self.cache_dir}")
                
        except Exception as e:
            logger.warning(f"Failed to initialize cache directory: {e}")
            self.cache_enabled = False
    
    def generate_cache_key(self, base_prompt: str, style: str, prompt_type: str) -> str:
        """
        Generate a unique cache key for the given inputs.
        
        Args:
            base_prompt: The original prompt text
            style: The style guidelines text
            prompt_type: Type of prompt (designer, writer, title, translator)
            
        Returns:
            Unique cache key string
        """
        # Combine inputs with separator to avoid collisions
        content = f"{base_prompt}|{style}|{prompt_type}"
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return f"{prompt_type}_{hash_obj.hexdigest()[:16]}"
    
    def get_cached_prompt(self, cache_key: str) -> Optional[str]:
        """
        Retrieve a cached prompt if it exists and is valid.
        
        This is the ONLY caching system that validates JSON content.
        SOURCE OF TRUTH: Both file existence AND JSON content validation.
        
        Args:
            cache_key: The cache key to look up
            
        Returns:
            Cached rewritten prompt or None if not found/invalid
        """
        if not self.cache_enabled:
            return None
            
        try:
            cache_file = self.cache_dir / f"{cache_key}.cache"
            
            if not cache_file.exists():
                return None
            
            # Load and validate cache entry
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    entry_data = json.load(f)
                    entry = CacheEntry(**entry_data)
            except (json.JSONDecodeError, TypeError, ValueError) as parse_error:
                logger.warning(f"Corrupted cache file {cache_key}: {parse_error}")
                # Delete corrupted file
                try:
                    cache_file.unlink()
                except Exception:
                    pass
                return None
            
            # Check if entry is expired
            if self._is_entry_expired(entry):
                logger.debug(f"Cache entry expired: {cache_key}")
                try:
                    cache_file.unlink()  # Delete expired entry
                except Exception:
                    pass
                return None
            
            # Update access time (ignore failures)
            try:
                entry.accessed_at = datetime.now().isoformat()
                self._save_cache_entry(entry)
            except Exception as update_error:
                logger.debug(f"Failed to update access time for {cache_key}: {update_error}")
            
            # Update metadata (ignore failures)
            try:
                self._increment_cache_hits()
            except Exception:
                pass
            
            logger.info(f"✓ Cache hit: {cache_key}")
            return entry.rewritten_prompt
            
        except Exception as e:
            logger.warning(f"Failed to retrieve cached prompt {cache_key}: {e}")
            return None
    
    def store_prompt(self, cache_key: str, rewritten_prompt: str, prompt_type: str, 
                    base_prompt: str, style: str) -> bool:
        """
        Store a rewritten prompt in the cache.
        
        Args:
            cache_key: The cache key
            rewritten_prompt: The rewritten prompt text
            prompt_type: Type of prompt (designer, writer, title, translator)
            base_prompt: Original prompt for metadata
            style: Style guidelines for metadata
            
        Returns:
            True if successfully stored, False otherwise
        """
        if not self.cache_enabled:
            return False
            
        try:
            # Check cache size before storing
            self._cleanup_cache_if_needed()
            
            # Create cache entry
            entry = CacheEntry(
                cache_key=cache_key,
                prompt_type=prompt_type,
                base_prompt_hash=hashlib.sha256(base_prompt.encode()).hexdigest()[:16],
                style_hash=hashlib.sha256(style.encode()).hexdigest()[:16],
                rewritten_prompt=rewritten_prompt,
                created_at=datetime.now().isoformat(),
                accessed_at=datetime.now().isoformat()
            )
            
            # Save cache entry
            self._save_cache_entry(entry)
            
            # Update metadata (ignore failures)
            try:
                self._increment_cache_misses()
                self._update_total_entries()
            except Exception:
                pass
            
            logger.info(f"✓ Cached prompt: {cache_key} ({len(rewritten_prompt)} chars)")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to store prompt in cache {cache_key}: {e}")
            return False
    
    def _save_cache_entry(self, entry: CacheEntry) -> None:
        """Save a cache entry to disk using atomic write."""
        cache_file = self.cache_dir / f"{entry.cache_key}.cache"
        temp_file = cache_file.with_suffix('.tmp')
        
        try:
            # Write to temporary file first
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(entry), f, indent=2, ensure_ascii=False)
            
            # Atomic move to final location
            temp_file.replace(cache_file)
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _is_entry_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired based on TTL."""
        try:
            created_time = datetime.fromisoformat(entry.created_at)
            expiry_time = created_time + timedelta(days=self.ttl_days)
            return datetime.now() > expiry_time
        except Exception:
            # If we can't parse the date, consider it expired
            return True
    
    def _load_metadata(self) -> CacheMetadata:
        """Load cache metadata from disk."""
        metadata_path = self.cache_dir / "cache_metadata.json"
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return CacheMetadata(**data)
        except Exception:
            # Return default metadata if loading fails
            return CacheMetadata()
    
    def _save_metadata(self, metadata: CacheMetadata) -> None:
        """Save cache metadata to disk."""
        metadata_path = self.cache_dir / "cache_metadata.json"
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache metadata: {e}")
    
    def _increment_cache_hits(self) -> None:
        """Increment cache hit counter in metadata."""
        try:
            metadata = self._load_metadata()
            metadata.cache_hits += 1
            self._save_metadata(metadata)
        except Exception as e:
            logger.debug(f"Failed to update cache hit counter: {e}")
    
    def _increment_cache_misses(self) -> None:
        """Increment cache miss counter in metadata."""
        try:
            metadata = self._load_metadata()
            metadata.cache_misses += 1
            self._save_metadata(metadata)
        except Exception as e:
            logger.debug(f"Failed to update cache miss counter: {e}")
    
    def _update_total_entries(self) -> None:
        """Update total entries count in metadata."""
        try:
            # Count actual cache files
            cache_files = list(self.cache_dir.glob("*.cache"))
            metadata = self._load_metadata()
            metadata.total_entries = len(cache_files)
            self._save_metadata(metadata)
        except Exception as e:
            logger.debug(f"Failed to update total entries count: {e}")
    
    def is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if a cache entry exists and is valid.
        
        Args:
            cache_key: The cache key to check
            
        Returns:
            True if cache entry exists and is valid
        """
        if not self.cache_enabled:
            return False
            
        try:
            cache_file = self.cache_dir / f"{cache_key}.cache"
            if not cache_file.exists():
                return False
                
            # Load and check expiry
            with open(cache_file, 'r', encoding='utf-8') as f:
                entry_data = json.load(f)
                entry = CacheEntry(**entry_data)
                
            return not self._is_entry_expired(entry)
            
        except Exception:
            return False
    
    def clear_cache(self) -> None:
        """Clear all cached entries."""
        try:
            # Remove all cache files
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            
            # Reset metadata
            metadata = CacheMetadata(
                created_at=datetime.now().isoformat(),
                last_cleanup=datetime.now().isoformat()
            )
            self._save_metadata(metadata)
            
            logger.info("Cache cleared successfully")
            
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
    
    def _cleanup_cache_if_needed(self) -> None:
        """Clean up cache if it exceeds size limits."""
        try:
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > self.max_size_mb:
                logger.info(f"Cache size ({total_size_mb:.1f}MB) exceeds limit ({self.max_size_mb}MB), cleaning up")
                
                # Sort files by access time (oldest first)
                files_with_time = []
                for cache_file in cache_files:
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            entry_data = json.load(f)
                            accessed_at = entry_data.get('accessed_at', entry_data.get('created_at', ''))
                            files_with_time.append((cache_file, accessed_at))
                    except Exception:
                        # If we can't read the file, mark it for deletion
                        files_with_time.append((cache_file, '1970-01-01'))
                
                # Sort by access time
                files_with_time.sort(key=lambda x: x[1])
                
                # Delete oldest files until we're under the limit
                deleted_count = 0
                for cache_file, _ in files_with_time:
                    try:
                        cache_file.unlink()
                        deleted_count += 1
                        
                        # Check if we're now under the limit
                        remaining_files = [f for f, _ in files_with_time[deleted_count:]]
                        if remaining_files:
                            remaining_size = sum(f.stat().st_size for f in remaining_files if f.exists())
                            if remaining_size / (1024 * 1024) <= self.max_size_mb * 0.8:  # 80% of limit
                                break
                    except Exception as e:
                        logger.debug(f"Failed to delete cache file {cache_file}: {e}")
                
                logger.info(f"Deleted {deleted_count} old cache entries")
                
                # Update metadata
                metadata = self._load_metadata()
                metadata.last_cleanup = datetime.now().isoformat()
                self._save_metadata(metadata)
                
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            metadata = self._load_metadata()
            cache_files = list(self.cache_dir.glob("*.cache"))
            
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "enabled": self.cache_enabled,
                "total_entries": len(cache_files),
                "cache_hits": metadata.cache_hits,
                "cache_misses": metadata.cache_misses,
                "hit_rate": metadata.cache_hits / max(1, metadata.cache_hits + metadata.cache_misses),
                "total_size_mb": total_size / (1024 * 1024),
                "max_size_mb": self.max_size_mb,
                "cache_dir": str(self.cache_dir),
                "created_at": metadata.created_at,
                "last_cleanup": metadata.last_cleanup
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {"enabled": self.cache_enabled, "error": str(e)}
    
    def log_performance_summary(self):
        """Log a performance summary for monitoring."""
        stats = self.get_cache_stats()
        
        if not stats.get('enabled'):
            logger.info("Cache Performance: DISABLED")
            return
        
        total_requests = stats.get('cache_hits', 0) + stats.get('cache_misses', 0)
        hit_rate = stats.get('hit_rate', 0)
        
        logger.info("=" * 60)
        logger.info("CACHE PERFORMANCE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Status: {'ENABLED' if stats.get('enabled') else 'DISABLED'}")
        logger.info(f"Total Requests: {total_requests}")
        logger.info(f"Cache Hits: {stats.get('cache_hits', 0)}")
        logger.info(f"Cache Misses: {stats.get('cache_misses', 0)}")
        logger.info(f"Hit Rate: {hit_rate:.1%}")
        logger.info(f"Efficiency Rating: {'EXCELLENT' if hit_rate > 0.8 else 'GOOD' if hit_rate > 0.5 else 'NEEDS IMPROVEMENT'}")
        logger.info(f"Storage: {stats.get('total_size_mb', 0):.2f}MB / {stats.get('max_size_mb', 0)}MB")
        logger.info(f"Entries: {stats.get('total_entries', 0)}")
        logger.info(f"Directory: {stats.get('cache_dir', 'N/A')}")
        
        if hit_rate > 0:
            estimated_time_saved = stats.get('cache_hits', 0) * 15  # Assume 15s per LLM call saved
            logger.info(f"Estimated Time Saved: {estimated_time_saved}s ({estimated_time_saved/60:.1f} min)")
        
        logger.info("=" * 60)