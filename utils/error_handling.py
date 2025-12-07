"""Error handling and retry utilities."""

import asyncio
import logging
from typing import Callable, TypeVar, Optional, Any
from functools import wraps

from config.constants import ProcessingConfig

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy:
    """Configurable retry strategy with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = ProcessingConfig.MAX_RETRIES,
        base_delay: float = ProcessingConfig.RETRY_DELAY,
        backoff_multiplier: float = ProcessingConfig.RETRY_BACKOFF_MULTIPLIER,
        exceptions: tuple = (Exception,),
    ):
        """
        Initialize retry strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            backoff_multiplier: Multiplier for exponential backoff
            exceptions: Tuple of exception types to catch and retry
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_multiplier = backoff_multiplier
        self.exceptions = exceptions
    
    async def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> Optional[T]:
        """
        Execute a function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func, or None if all retries failed
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(
                        f"Successfully executed {func.__name__} "
                        f"on attempt {attempt + 1}"
                    )
                return result
                
            except self.exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (
                        self.backoff_multiplier ** attempt
                    )
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed "
                        f"for {func.__name__}: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"All {self.max_retries} attempts failed "
                        f"for {func.__name__}: {e}"
                    )
        
        return None


def with_retry(
    max_retries: int = ProcessingConfig.MAX_RETRIES,
    base_delay: float = ProcessingConfig.RETRY_DELAY,
    exceptions: tuple = (Exception,),
):
    """
    Decorator to add retry logic to async functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries
        exceptions: Tuple of exception types to catch
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            strategy = RetryStrategy(
                max_retries=max_retries,
                base_delay=base_delay,
                exceptions=exceptions,
            )
            return await strategy.execute(func, *args, **kwargs)
        return wrapper
    return decorator


class ProcessingError(Exception):
    """Base exception for processing errors."""
    pass


class SlideProcessingError(ProcessingError):
    """Error processing a specific slide."""
    
    def __init__(self, slide_idx: int, message: str):
        self.slide_idx = slide_idx
        super().__init__(f"Slide {slide_idx}: {message}")


class TranslationError(ProcessingError):
    """Error during translation."""
    pass


class VisualGenerationError(ProcessingError):
    """Error during visual generation."""
    pass


class VideoGenerationError(ProcessingError):
    """Error during video generation."""
    pass
