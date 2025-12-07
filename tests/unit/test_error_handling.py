"""Tests for error handling utilities."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from utils.error_handling import (
    RetryStrategy,
    with_retry,
    ProcessingError,
    SlideProcessingError,
    TranslationError,
    VisualGenerationError,
    VideoGenerationError,
)


class TestRetryStrategy:
    """Tests for RetryStrategy class."""
    
    @pytest.mark.asyncio
    async def test_execute_success_first_try(self):
        """Test successful execution on first try."""
        async def success_func():
            return "success"
        
        strategy = RetryStrategy(max_retries=3)
        result = await strategy.execute(success_func)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execute_success_after_retry(self):
        """Test successful execution after retries."""
        call_count = 0
        
        async def retry_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"
        
        strategy = RetryStrategy(max_retries=3, base_delay=0.01)
        result = await strategy.execute(retry_func)
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_all_retries_fail(self):
        """Test when all retries fail."""
        async def fail_func():
            raise ValueError("Permanent error")
        
        strategy = RetryStrategy(max_retries=2, base_delay=0.01)
        result = await strategy.execute(fail_func)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_execute_with_args(self):
        """Test execution with arguments."""
        async def func_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"
        
        strategy = RetryStrategy()
        result = await strategy.execute(func_with_args, "x", "y", c="z")
        
        assert result == "x-y-z"
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff timing."""
        call_times = []
        
        async def timed_func():
            call_times.append(asyncio.get_event_loop().time())
            raise ValueError("Error")
        
        strategy = RetryStrategy(
            max_retries=3,
            base_delay=0.1,
            backoff_multiplier=2.0
        )
        
        await strategy.execute(timed_func)
        
        # Should have 3 calls
        assert len(call_times) == 3
        
        # Check delays are increasing
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert delay1 >= 0.09  # ~0.1s with some tolerance
    
    @pytest.mark.asyncio
    async def test_custom_exceptions(self):
        """Test retry only on specific exceptions."""
        call_count = 0
        
        async def custom_exception_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retry this")
            raise TypeError("Don't retry this")
        
        strategy = RetryStrategy(
            max_retries=3,
            base_delay=0.01,
            exceptions=(ValueError,)
        )
        
        result = await strategy.execute(custom_exception_func)
        
        # Should fail on TypeError without retrying
        assert result is None
        assert call_count == 2  # First ValueError, then TypeError


class TestWithRetryDecorator:
    """Tests for @with_retry decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test decorator with successful function."""
        @with_retry(max_retries=3)
        async def success_func():
            return "decorated success"
        
        result = await success_func()
        assert result == "decorated success"
    
    @pytest.mark.asyncio
    async def test_decorator_with_retry(self):
        """Test decorator retries on failure."""
        call_count = 0
        
        @with_retry(max_retries=3, base_delay=0.01)
        async def retry_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retry")
            return "success after retry"
        
        result = await retry_func()
        
        assert result == "success after retry"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_decorator_with_args(self):
        """Test decorator preserves function arguments."""
        @with_retry(max_retries=2)
        async def func_with_args(x, y, z=10):
            return x + y + z
        
        result = await func_with_args(1, 2, z=3)
        assert result == 6


class TestCustomExceptions:
    """Tests for custom exception classes."""
    
    def test_processing_error(self):
        """Test ProcessingError exception."""
        error = ProcessingError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_slide_processing_error(self):
        """Test SlideProcessingError exception."""
        error = SlideProcessingError(5, "Slide failed")
        assert error.slide_idx == 5
        assert "Slide 5" in str(error)
        assert "Slide failed" in str(error)
        assert isinstance(error, ProcessingError)
    
    def test_translation_error(self):
        """Test TranslationError exception."""
        error = TranslationError("Translation failed")
        assert str(error) == "Translation failed"
        assert isinstance(error, ProcessingError)
    
    def test_visual_generation_error(self):
        """Test VisualGenerationError exception."""
        error = VisualGenerationError("Visual failed")
        assert str(error) == "Visual failed"
        assert isinstance(error, ProcessingError)
    
    def test_video_generation_error(self):
        """Test VideoGenerationError exception."""
        error = VideoGenerationError("Video failed")
        assert str(error) == "Video failed"
        assert isinstance(error, ProcessingError)
    
    def test_exception_hierarchy(self):
        """Test exception hierarchy."""
        # All custom exceptions should inherit from ProcessingError
        assert issubclass(SlideProcessingError, ProcessingError)
        assert issubclass(TranslationError, ProcessingError)
        assert issubclass(VisualGenerationError, ProcessingError)
        assert issubclass(VideoGenerationError, ProcessingError)
        
        # ProcessingError should inherit from Exception
        assert issubclass(ProcessingError, Exception)
