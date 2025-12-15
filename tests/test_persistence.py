#!/usr/bin/env python3
"""Test cache persistence and configuration."""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from services.prompt_cache import PromptCache


def test_cache_persistence():
    """Test that cache persists across restarts."""
    print("Testing cache persistence...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create first cache instance and store data
        cache1 = PromptCache(cache_dir=temp_dir)
        
        cache_key = cache1.generate_cache_key("test prompt", "test style", "test")
        success = cache1.store_prompt(cache_key, "rewritten prompt", "test", "test prompt", "test style")
        assert success, "Failed to store prompt"
        
        stats1 = cache1.get_cache_stats()
        print(f"Cache stats after storing: {stats1}")
        
        # Create second cache instance (simulating restart)
        cache2 = PromptCache(cache_dir=temp_dir)
        
        # Should be able to retrieve the cached prompt
        result = cache2.get_cached_prompt(cache_key)
        assert result == "rewritten prompt", "Cache should persist across restarts"
        
        stats2 = cache2.get_cache_stats()
        print(f"Cache stats after restart: {stats2}")
        
        # Should have the same entry count
        assert stats2['total_entries'] == 1, "Should have 1 entry after restart"
        
        print("✓ Cache persistence works correctly")


def test_environment_configuration():
    """Test environment variable configuration."""
    print("Testing environment variable configuration...")
    
    # Set custom environment variables
    os.environ['PROMPT_CACHE_ENABLED'] = 'false'
    os.environ['PROMPT_CACHE_MAX_SIZE_MB'] = '50'
    os.environ['PROMPT_CACHE_TTL_DAYS'] = '7'
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['PROMPT_CACHE_DIR'] = temp_dir
        
        cache = PromptCache()
        
        # Check configuration
        assert not cache.cache_enabled, "Cache should be disabled"
        assert cache.max_size_mb == 50, "Max size should be 50MB"
        assert cache.ttl_days == 7, "TTL should be 7 days"
        assert str(cache.cache_dir) == temp_dir, "Cache dir should match env var"
        
        print("✓ Environment variable configuration works correctly")
    
    # Clean up environment variables
    for var in ['PROMPT_CACHE_ENABLED', 'PROMPT_CACHE_MAX_SIZE_MB', 'PROMPT_CACHE_TTL_DAYS', 'PROMPT_CACHE_DIR']:
        if var in os.environ:
            del os.environ[var]


def test_cache_statistics():
    """Test cache statistics tracking."""
    print("Testing cache statistics...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = PromptCache(cache_dir=temp_dir)
        
        # Initial stats
        stats = cache.get_cache_stats()
        assert stats['cache_hits'] == 0, "Should start with 0 hits"
        assert stats['cache_misses'] == 0, "Should start with 0 misses"
        
        # Store and retrieve
        cache_key = cache.generate_cache_key("test", "style", "type")
        cache.store_prompt(cache_key, "result", "type", "test", "style")
        
        # Cache miss should be recorded
        stats = cache.get_cache_stats()
        assert stats['cache_misses'] == 1, "Should have 1 miss after store"
        
        # Retrieve (cache hit)
        result = cache.get_cached_prompt(cache_key)
        assert result == "result", "Should retrieve cached result"
        
        # Cache hit should be recorded
        stats = cache.get_cache_stats()
        assert stats['cache_hits'] == 1, "Should have 1 hit after retrieval"
        assert stats['hit_rate'] == 0.5, "Hit rate should be 50%"
        
        print("✓ Cache statistics tracking works correctly")


def test_cache_metadata_persistence():
    """Test that metadata persists across restarts."""
    print("Testing metadata persistence...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create cache and generate some activity
        cache1 = PromptCache(cache_dir=temp_dir)
        
        cache_key = cache1.generate_cache_key("test", "style", "type")
        cache1.store_prompt(cache_key, "result", "type", "test", "style")
        cache1.get_cached_prompt(cache_key)  # Generate a hit
        
        stats1 = cache1.get_cache_stats()
        
        # Create new cache instance
        cache2 = PromptCache(cache_dir=temp_dir)
        stats2 = cache2.get_cache_stats()
        
        # Metadata should persist
        assert stats2['cache_hits'] == stats1['cache_hits'], "Cache hits should persist"
        assert stats2['cache_misses'] == stats1['cache_misses'], "Cache misses should persist"
        assert stats2['created_at'] == stats1['created_at'], "Created time should persist"
        
        print("✓ Metadata persistence works correctly")


if __name__ == "__main__":
    try:
        test_cache_persistence()
        test_environment_configuration()
        test_cache_statistics()
        test_cache_metadata_persistence()
        print("\n🎉 All persistence and configuration tests passed!")
    except Exception as e:
        print(f"\n❌ Persistence test failed: {e}")
        sys.exit(1)