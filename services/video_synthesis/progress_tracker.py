"""Progress tracking and error reporting for video synthesis."""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
import threading

logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Stages of video synthesis processing."""
    INITIALIZING = "initializing"
    VALIDATING = "validating"
    ANALYZING_AUDIO = "analyzing_audio"
    CREATING_SEGMENTS = "creating_segments"
    CONCATENATING = "concatenating"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressUpdate:
    """Progress update information."""
    stage: ProcessingStage
    current_slide: Optional[int] = None
    total_slides: Optional[int] = None
    progress_percentage: float = 0.0
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_progress_text(self) -> str:
        """Get human-readable progress text."""
        if self.current_slide is not None and self.total_slides is not None:
            return f"{self.stage.value.title()}: Slide {self.current_slide}/{self.total_slides} ({self.progress_percentage:.1f}%)"
        else:
            return f"{self.stage.value.title()}: {self.progress_percentage:.1f}%"


@dataclass
class ErrorInfo:
    """Error information with context."""
    error_type: str
    error_message: str
    slide_index: Optional[int] = None
    stage: Optional[ProcessingStage] = None
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def get_detailed_message(self) -> str:
        """Get detailed error message with context."""
        parts = [f"{self.error_type}: {self.error_message}"]
        
        if self.slide_index is not None:
            parts.append(f"Slide: {self.slide_index}")
        
        if self.stage:
            parts.append(f"Stage: {self.stage.value}")
        
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")
        
        return " | ".join(parts)


class VideoProgressTracker:
    """Progress tracker for video synthesis operations."""
    
    def __init__(self, operation_id: str, total_slides: int):
        """
        Initialize progress tracker.
        
        Args:
            operation_id: Unique identifier for the operation
            total_slides: Total number of slides to process
        """
        self.operation_id = operation_id
        self.total_slides = total_slides
        self.current_stage = ProcessingStage.INITIALIZING
        self.current_slide = 0
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        
        # Progress tracking
        self.progress_history: List[ProgressUpdate] = []
        self.error_history: List[ErrorInfo] = []
        self.is_cancelled = False
        
        # Callbacks for progress updates
        self.progress_callbacks: List[Callable[[ProgressUpdate], None]] = []
        self.error_callbacks: List[Callable[[ErrorInfo], None]] = []
        
        # Thread safety
        self.lock = threading.Lock()
        
        logger.info(f"Initialized progress tracker for operation {operation_id} with {total_slides} slides")
    
    def add_progress_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """
        Add callback for progress updates.
        
        Args:
            callback: Function to call on progress updates
        """
        with self.lock:
            self.progress_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[ErrorInfo], None]) -> None:
        """
        Add callback for error notifications.
        
        Args:
            callback: Function to call on errors
        """
        with self.lock:
            self.error_callbacks.append(callback)
    
    def update_stage(self, stage: ProcessingStage, message: str = "", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update current processing stage.
        
        Args:
            stage: New processing stage
            message: Optional progress message
            metadata: Optional metadata dictionary
        """
        with self.lock:
            if self.is_cancelled:
                return
            
            self.current_stage = stage
            
            # Calculate progress percentage based on stage
            stage_progress = self._calculate_stage_progress(stage)
            
            progress_update = ProgressUpdate(
                stage=stage,
                current_slide=self.current_slide if self.current_slide > 0 else None,
                total_slides=self.total_slides,
                progress_percentage=stage_progress,
                message=message,
                metadata=metadata or {}
            )
            
            self.progress_history.append(progress_update)
            
            logger.info(f"Operation {self.operation_id}: {progress_update.get_progress_text()}")
            if message:
                logger.info(f"  Message: {message}")
            
            # Notify callbacks
            for callback in self.progress_callbacks:
                try:
                    callback(progress_update)
                except Exception as e:
                    logger.warning(f"Error in progress callback (non-critical): {e}")
                    logger.debug(f"Callback: {callback}, Update type: {type(progress_update)}")
    
    def update_slide_progress(self, slide_index: int, stage: ProcessingStage, message: str = "", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update progress for specific slide.
        
        Args:
            slide_index: Current slide index (0-based)
            stage: Current processing stage
            message: Optional progress message
            metadata: Optional metadata dictionary
        """
        with self.lock:
            if self.is_cancelled:
                return
            
            self.current_slide = slide_index + 1  # Convert to 1-based for display
            self.current_stage = stage
            
            # Calculate progress percentage
            slide_progress = (slide_index / self.total_slides) * 100
            stage_progress = self._calculate_stage_progress(stage)
            total_progress = (slide_progress + stage_progress) / 2
            
            progress_update = ProgressUpdate(
                stage=stage,
                current_slide=self.current_slide,
                total_slides=self.total_slides,
                progress_percentage=total_progress,
                message=message,
                metadata=metadata or {}
            )
            
            self.progress_history.append(progress_update)
            
            logger.debug(f"Operation {self.operation_id}: {progress_update.get_progress_text()}")
            if message:
                logger.debug(f"  Message: {message}")
            
            # Notify callbacks
            for callback in self.progress_callbacks:
                try:
                    callback(progress_update)
                except Exception as e:
                    logger.warning(f"Error in progress callback (non-critical): {e}")
                    logger.debug(f"Callback: {callback}, Update type: {type(progress_update)}")
    
    def report_error(self, error: Exception, slide_index: Optional[int] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Report an error during processing.
        
        Args:
            error: Exception that occurred
            slide_index: Optional slide index where error occurred
            context: Optional context information
        """
        with self.lock:
            error_info = ErrorInfo(
                error_type=type(error).__name__,
                error_message=str(error),
                slide_index=slide_index,
                stage=self.current_stage,
                context=context or {}
            )
            
            self.error_history.append(error_info)
            
            logger.error(f"Operation {self.operation_id}: {error_info.get_detailed_message()}")
            
            # Notify callbacks
            for callback in self.error_callbacks:
                try:
                    callback(error_info)
                except Exception as e:
                    logger.error(f"Error in error callback: {e}")
    
    def mark_completed(self, output_path: Path, file_size: int, duration: float) -> None:
        """
        Mark operation as completed successfully.
        
        Args:
            output_path: Path to output video file
            file_size: Size of output file in bytes
            duration: Duration of output video in seconds
        """
        with self.lock:
            if self.is_cancelled:
                return
            
            self.end_time = time.time()
            processing_time = self.end_time - self.start_time
            
            completion_metadata = {
                'output_path': str(output_path),
                'file_size_bytes': file_size,
                'video_duration_seconds': duration,
                'processing_time_seconds': processing_time,
                'slides_processed': self.total_slides
            }
            
            self.update_stage(
                ProcessingStage.COMPLETED,
                f"Video synthesis completed successfully. Output: {output_path.name}",
                completion_metadata
            )
            
            logger.info(f"Operation {self.operation_id} completed successfully in {processing_time:.2f}s")
            logger.info(f"  Output: {output_path}")
            logger.info(f"  File size: {file_size / (1024*1024):.2f} MB")
            logger.info(f"  Duration: {duration:.2f} seconds")
    
    def mark_failed(self, error: Exception, slide_index: Optional[int] = None) -> None:
        """
        Mark operation as failed.
        
        Args:
            error: Exception that caused the failure
            slide_index: Optional slide index where failure occurred
        """
        with self.lock:
            self.end_time = time.time()
            processing_time = self.end_time - self.start_time
            
            # Report the error
            self.report_error(error, slide_index, {'processing_time_seconds': processing_time})
            
            # Update stage to failed
            self.update_stage(
                ProcessingStage.FAILED,
                f"Video synthesis failed: {str(error)}",
                {'processing_time_seconds': processing_time}
            )
            
            logger.error(f"Operation {self.operation_id} failed after {processing_time:.2f}s: {error}")
    
    def mark_cancelled(self, cleanup_status: Dict[str, Any]) -> None:
        """
        Mark operation as cancelled.
        
        Args:
            cleanup_status: Status of cleanup operations
        """
        with self.lock:
            self.is_cancelled = True
            self.end_time = time.time()
            processing_time = self.end_time - self.start_time
            
            cancellation_metadata = {
                'processing_time_seconds': processing_time,
                'cleanup_status': cleanup_status
            }
            
            self.update_stage(
                ProcessingStage.CANCELLED,
                "Video synthesis cancelled by user",
                cancellation_metadata
            )
            
            logger.info(f"Operation {self.operation_id} cancelled after {processing_time:.2f}s")
    
    def _calculate_stage_progress(self, stage: ProcessingStage) -> float:
        """
        Calculate progress percentage based on processing stage.
        
        Args:
            stage: Current processing stage
            
        Returns:
            Progress percentage (0-100)
        """
        stage_weights = {
            ProcessingStage.INITIALIZING: 5,
            ProcessingStage.VALIDATING: 10,
            ProcessingStage.ANALYZING_AUDIO: 15,
            ProcessingStage.CREATING_SEGMENTS: 60,
            ProcessingStage.CONCATENATING: 85,
            ProcessingStage.FINALIZING: 95,
            ProcessingStage.COMPLETED: 100,
            ProcessingStage.FAILED: 0,
            ProcessingStage.CANCELLED: 0
        }
        
        return stage_weights.get(stage, 0)
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current status summary.
        
        Returns:
            Dictionary with current status information
        """
        with self.lock:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            
            latest_progress = self.progress_history[-1] if self.progress_history else None
            latest_error = self.error_history[-1] if self.error_history else None
            
            status = {
                'operation_id': self.operation_id,
                'stage': self.current_stage.value,
                'current_slide': self.current_slide,
                'total_slides': self.total_slides,
                'progress_percentage': latest_progress.progress_percentage if latest_progress else 0,
                'elapsed_time_seconds': elapsed_time,
                'is_completed': self.current_stage in [ProcessingStage.COMPLETED, ProcessingStage.FAILED, ProcessingStage.CANCELLED],
                'is_cancelled': self.is_cancelled,
                'error_count': len(self.error_history)
            }
            
            if latest_progress:
                status['latest_message'] = latest_progress.message
                status['latest_update_time'] = latest_progress.timestamp
            
            if latest_error:
                status['latest_error'] = latest_error.get_detailed_message()
                status['latest_error_time'] = latest_error.timestamp
            
            return status
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """
        Get detailed progress report.
        
        Returns:
            Dictionary with comprehensive progress information
        """
        with self.lock:
            current_time = time.time()
            elapsed_time = current_time - self.start_time
            
            report = {
                'operation_id': self.operation_id,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'elapsed_time_seconds': elapsed_time,
                'total_slides': self.total_slides,
                'current_stage': self.current_stage.value,
                'is_completed': self.current_stage in [ProcessingStage.COMPLETED, ProcessingStage.FAILED, ProcessingStage.CANCELLED],
                'is_cancelled': self.is_cancelled,
                'progress_updates_count': len(self.progress_history),
                'error_count': len(self.error_history)
            }
            
            # Add progress history
            report['progress_history'] = [
                {
                    'stage': update.stage.value,
                    'current_slide': update.current_slide,
                    'progress_percentage': update.progress_percentage,
                    'message': update.message,
                    'timestamp': update.timestamp,
                    'metadata': update.metadata
                }
                for update in self.progress_history
            ]
            
            # Add error history
            report['error_history'] = [
                {
                    'error_type': error.error_type,
                    'error_message': error.error_message,
                    'slide_index': error.slide_index,
                    'stage': error.stage.value if error.stage else None,
                    'timestamp': error.timestamp,
                    'context': error.context
                }
                for error in self.error_history
            ]
            
            return report


class ProgressReporter:
    """Simple progress reporter with console output."""
    
    def __init__(self, show_detailed: bool = False):
        """
        Initialize progress reporter.
        
        Args:
            show_detailed: Whether to show detailed progress information
        """
        self.show_detailed = show_detailed
        self.last_progress_time = 0
        self.min_update_interval = 1.0  # Minimum seconds between updates
    
    def on_progress_update(self, update: ProgressUpdate) -> None:
        """
        Handle progress update.
        
        Args:
            update: Progress update information
        """
        current_time = time.time()
        
        # Throttle updates to avoid spam
        if current_time - self.last_progress_time < self.min_update_interval:
            return
        
        self.last_progress_time = current_time
        
        if self.show_detailed:
            print(f"[{update.timestamp:.0f}] {update.get_progress_text()}")
            if update.message:
                print(f"  {update.message}")
        else:
            print(f"\r{update.get_progress_text()}", end="", flush=True)
    
    def on_error(self, error: ErrorInfo) -> None:
        """
        Handle error notification.
        
        Args:
            error: Error information
        """
        print(f"\nERROR: {error.get_detailed_message()}")
    
    def on_completion(self, final_status: Dict[str, Any]) -> None:
        """
        Handle completion notification.
        
        Args:
            final_status: Final status information
        """
        if final_status.get('is_completed'):
            if final_status['stage'] == 'completed':
                print(f"\n✓ Video synthesis completed successfully!")
                if 'latest_message' in final_status:
                    print(f"  {final_status['latest_message']}")
            elif final_status['stage'] == 'failed':
                print(f"\n✗ Video synthesis failed!")
                if 'latest_error' in final_status:
                    print(f"  {final_status['latest_error']}")
            elif final_status['stage'] == 'cancelled':
                print(f"\n⚠ Video synthesis cancelled!")
        
        elapsed = final_status.get('elapsed_time_seconds', 0)
        print(f"  Total time: {elapsed:.2f} seconds")