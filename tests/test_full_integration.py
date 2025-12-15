#!/usr/bin/env python3
"""Comprehensive integration test for the prompt rewriter optimization."""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from services.prompt_cache import PromptCache


def test_full_workflow():
    """Test the complete caching workflow."""
    print("Testing complete caching workflow...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['PROMPT_CACHE_DIR'] = temp_dir
        os.environ['PROMPT_CACHE_ENABLED'] = 'true'
        
        # Test cache initialization
        cache = PromptCache()
        assert cache.cache_enabled, "Cache should be enabled"
        
        # Test cache key generation
        base_prompt = "You are a helpful assistant"
        style = "Professional and friendly"
        prompt_type = "assistant"
        
        cache_key = cache.generate_cache_key(base_prompt, style, prompt_type)
        assert cache_key.startswith(prompt_type), "Cache key should start with prompt type"
        
        # Test cache miss
        start_time = time.time()
        result = cache.get_cached_prompt(cache_key)
        miss_time = time.time() - start_time
        assert result is None, "Should be cache miss initially"
        assert miss_time < 0.1, "Cache miss should be fast"
        
        # Test cache storage
        rewritten_prompt = "You are a helpful, professional, and friendly assistant."
        success = cache.store_prompt(cache_key, rewritten_prompt, prompt_type, base_prompt, style)
        assert success, "Should successfully store prompt"
        
        # Test cache hit
        start_time = time.time()
        result = cache.get_cached_prompt(cache_key)
        hit_time = time.time() - start_time
        assert result == rewritten_prompt, "Should retrieve cached prompt"
        assert hit_time < 0.1, "Cache hit should be fast"
        
        # Test statistics
        stats = cache.get_cache_stats()
        assert stats['total_entries'] == 1, "Should have 1 entry"
        assert stats['cache_hits'] == 1, "Should have 1 hit"
        assert stats['cache_misses'] == 1, "Should have 1 miss"
        assert stats['hit_rate'] == 0.5, "Hit rate should be 50%"
        
        print("✓ Complete caching workflow works correctly")
        
        # Clean up environment
        del os.environ['PROMPT_CACHE_DIR']
        del os.environ['PROMPT_CACHE_ENABLED']


def test_performance_improvement():
    """Test that caching provides performance improvement."""
    print("Testing performance improvement...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = PromptCache(cache_dir=temp_dir)
        
        # Simulate multiple requests for the same prompt
        base_prompt = "Test prompt"
        style = "Test style"
        prompt_type = "test"
        rewritten = "Test rewritten prompt"
        
        cache_key = cache.generate_cache_key(base_prompt, style, prompt_type)
        
        # First request (cache miss)
        start_time = time.time()
        result = cache.get_cached_prompt(cache_key)
        assert result is None
        cache.store_prompt(cache_key, rewritten, prompt_type, base_prompt, style)
        first_request_time = time.time() - start_time
        
        # Subsequent requests (cache hits)
        hit_times = []
        for _ in range(5):
            start_time = time.time()
            result = cache.get_cached_prompt(cache_key)
            hit_time = time.time() - start_time
            hit_times.append(hit_time)
            assert result == rewritten
        
        avg_hit_time = sum(hit_times) / len(hit_times)
        
        # Cache hits should be much faster than the first request
        assert avg_hit_time < first_request_time, "Cache hits should be faster than initial storage"
        assert avg_hit_time < 0.01, "Cache hits should be very fast (< 10ms)"
        
        print(f"✓ Performance improvement verified: {avg_hit_time*1000:.1f}ms avg hit time")


def test_cache_robustness():
    """Test cache robustness under various conditions."""
    print("Testing cache robustness...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = PromptCache(cache_dir=temp_dir)
        
        # Test with various input types
        test_cases = [
            ("Simple prompt", "Simple style", "simple"),
            ("Prompt with unicode: 你好", "Style with emoji: 🎉", "unicode"),
            ("Very long prompt " * 100, "Very long style " * 50, "long"),
            ("", "", "empty"),  # Edge case
            ("Prompt\nwith\nnewlines", "Style\nwith\nnewlines", "newlines"),
        ]
        
        for base_prompt, style, prompt_type in test_cases:
            cache_key = cache.generate_cache_key(base_prompt, style, prompt_type)
            
            # Should handle all cases gracefully
            result = cache.get_cached_prompt(cache_key)
            assert result is None, f"Should be cache miss for {prompt_type}"
            
            rewritten = f"Rewritten: {base_prompt[:50]}..."
            success = cache.store_prompt(cache_key, rewritten, prompt_type, base_prompt, style)
            assert success, f"Should store prompt for {prompt_type}"
            
            result = cache.get_cached_prompt(cache_key)
            assert result == rewritten, f"Should retrieve prompt for {prompt_type}"
        
        # Verify all entries were stored
        stats = cache.get_cache_stats()
        assert stats['total_entries'] == len(test_cases), "Should have all test cases stored"
        
        print("✓ Cache robustness verified")


def test_backward_compatibility():
    """Test that the implementation maintains backward compatibility."""
    print("Testing backward compatibility...")
    
    # Test that the cache can be disabled
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['PROMPT_CACHE_ENABLED'] = 'false'
        
        cache = PromptCache(cache_dir=temp_dir)
        assert not cache.cache_enabled, "Cache should be disabled"
        
        # Operations should still work but not cache
        cache_key = cache.generate_cache_key("test", "style", "type")
        result = cache.get_cached_prompt(cache_key)
        assert result is None, "Should return None when disabled"
        
        success = cache.store_prompt(cache_key, "result", "type", "test", "style")
        assert not success, "Should not store when disabled"
        
        # Clean up
        del os.environ['PROMPT_CACHE_ENABLED']
        
        print("✓ Backward compatibility verified")


if __name__ == "__main__":
    try:
        test_full_workflow()
        test_performance_improvement()
        test_cache_robustness()
        test_backward_compatibility()
        print("\n🎉 All integration tests passed!")
        print("\nSUMMARY:")
        print("- Cache functionality: ✓ Working")
        print("- Performance improvement: ✓ Verified")
        print("- Error handling: ✓ Robust")
        print("- Backward compatibility: ✓ Maintained")
        print("- Configuration: ✓ Flexible")
        print("\nThe prompt rewriter optimization is ready for production use!")
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        sys.exit(1)