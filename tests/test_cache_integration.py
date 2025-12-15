#!/usr/bin/env python3
"""Simple test to verify prompt cache integration works."""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from services.prompt_cache import PromptCache


def test_cache_basic_functionality():
    """Test basic cache functionality."""
    print("Testing basic cache functionality...")
    
    # Create temporary cache directory
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = PromptCache(cache_dir=temp_dir)
        
        # Test cache key generation
        base_prompt = "You are a test prompt"
        style = "Professional style"
        prompt_type = "test"
        
        cache_key = cache.generate_cache_key(base_prompt, style, prompt_type)
        print(f"Generated cache key: {cache_key}")
        
        # Test cache miss
        result = cache.get_cached_prompt(cache_key)
        assert result is None, "Expected cache miss"
        print("✓ Cache miss works correctly")
        
        # Test cache storage
        test_prompt = "This is a rewritten test prompt"
        success = cache.store_prompt(cache_key, test_prompt, prompt_type, base_prompt, style)
        assert success, "Failed to store prompt"
        print("✓ Cache storage works correctly")
        
        # Test cache hit
        result = cache.get_cached_prompt(cache_key)
        assert result == test_prompt, f"Expected '{test_prompt}', got '{result}'"
        print("✓ Cache hit works correctly")
        
        # Test cache stats
        stats = cache.get_cache_stats()
        print(f"Cache stats: {stats}")
        assert stats['total_entries'] == 1, "Expected 1 cache entry"
        assert stats['cache_hits'] == 1, "Expected 1 cache hit"
        assert stats['cache_misses'] == 1, "Expected 1 cache miss"
        print("✓ Cache statistics work correctly")
        
    print("All cache tests passed!")


def test_prompt_rewriter_integration():
    """Test PromptRewriter with cache integration."""
    print("\nTesting PromptRewriter integration...")
    
    # Set environment variables for testing
    os.environ['PROMPT_CACHE_ENABLED'] = 'true'
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['PROMPT_CACHE_DIR'] = temp_dir
        
        # Import after setting environment variables
        from services.prompt_rewriter import PromptRewriter
        
        # Create rewriter with simple styles
        rewriter = PromptRewriter(
            visual_style="Simple visual style",
            speaker_style="Simple speaker style"
        )
        
        print("✓ PromptRewriter initialized with cache")
        
        # Check cache stats
        stats = rewriter.get_rewrite_summary()
        print(f"Rewriter summary: {stats}")
        assert 'cache_stats' in stats, "Cache stats not in summary"
        print("✓ Cache stats included in rewriter summary")
        
    print("PromptRewriter integration test passed!")


if __name__ == "__main__":
    try:
        test_cache_basic_functionality()
        test_prompt_rewriter_integration()
        print("\n🎉 All tests passed! Cache integration is working.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)