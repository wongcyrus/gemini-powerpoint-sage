#!/usr/bin/env python3
"""Test performance monitoring and logging."""

import os
import sys
import tempfile
import logging
from pathlib import Path
from io import StringIO

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from services.prompt_cache import PromptCache


def test_performance_logging():
    """Test performance logging functionality."""
    print("Testing performance logging...")
    
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger('services.prompt_cache')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PromptCache(cache_dir=temp_dir)
            
            # Generate some cache activity
            for i in range(3):
                cache_key = f"test_key_{i}"
                cache.store_prompt(cache_key, f"result_{i}", "test", f"prompt_{i}", "style")
            
            # Generate some hits
            cache.get_cached_prompt("test_key_0")
            cache.get_cached_prompt("test_key_1")
            
            # Log performance summary
            cache.log_performance_summary()
            
            # Check that performance metrics were logged
            log_output = log_capture.getvalue()
            assert "CACHE PERFORMANCE SUMMARY" in log_output, "Performance summary should be logged"
            assert "Hit Rate:" in log_output, "Hit rate should be logged"
            assert "Estimated Time Saved:" in log_output, "Time saved should be logged"
            
            print("✓ Performance logging works correctly")
            
    finally:
        logger.removeHandler(handler)


def test_cache_statistics_accuracy():
    """Test that cache statistics are accurate."""
    print("Testing cache statistics accuracy...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = PromptCache(cache_dir=temp_dir)
        
        # Perform known operations
        cache.store_prompt("key1", "result1", "test", "prompt1", "style")  # Miss
        cache.store_prompt("key2", "result2", "test", "prompt2", "style")  # Miss
        cache.get_cached_prompt("key1")  # Hit
        cache.get_cached_prompt("key1")  # Hit
        cache.get_cached_prompt("key3")  # Miss (not found)
        
        stats = cache.get_cache_stats()
        
        # Verify statistics
        assert stats['total_entries'] == 2, f"Expected 2 entries, got {stats['total_entries']}"
        assert stats['cache_hits'] == 2, f"Expected 2 hits, got {stats['cache_hits']}"
        assert stats['cache_misses'] == 2, f"Expected 2 misses, got {stats['cache_misses']}"
        assert abs(stats['hit_rate'] - 0.5) < 0.01, f"Expected 50% hit rate, got {stats['hit_rate']}"
        
        print("✓ Cache statistics accuracy verified")


def test_performance_metrics_calculation():
    """Test performance metrics calculations."""
    print("Testing performance metrics calculations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = PromptCache(cache_dir=temp_dir)
        
        # Create scenario with good hit rate
        for i in range(10):
            cache.store_prompt(f"key_{i}", f"result_{i}", "test", f"prompt_{i}", "style")
        
        # Generate many hits
        for i in range(10):
            for j in range(3):  # 3 hits per key
                cache.get_cached_prompt(f"key_{i}")
        
        stats = cache.get_cache_stats()
        
        # Should have high hit rate
        assert stats['hit_rate'] > 0.7, f"Expected high hit rate, got {stats['hit_rate']}"
        assert stats['cache_hits'] == 30, f"Expected 30 hits, got {stats['cache_hits']}"
        assert stats['cache_misses'] == 10, f"Expected 10 misses, got {stats['cache_misses']}"
        
        print("✓ Performance metrics calculations verified")


if __name__ == "__main__":
    try:
        test_performance_logging()
        test_cache_statistics_accuracy()
        test_performance_metrics_calculation()
        print("\n🎉 All performance monitoring tests passed!")
    except Exception as e:
        print(f"\n❌ Performance monitoring test failed: {e}")
        sys.exit(1)