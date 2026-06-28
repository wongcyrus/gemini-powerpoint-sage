"""Tests for video synthesis progress tracking."""

from pathlib import Path
from unittest.mock import Mock, patch

from services.video_synthesis.progress_tracker import (
    ErrorInfo,
    ProcessingStage,
    ProgressReporter,
    ProgressUpdate,
    VideoProgressTracker,
)


class TestProgressUpdateAndErrorInfo:
    """Tests for progress and error dataclasses."""

    def test_progress_text_with_slide(self):
        """Progress text should include slide info when available."""
        update = ProgressUpdate(
            stage=ProcessingStage.CREATING_SEGMENTS,
            current_slide=2,
            total_slides=5,
            progress_percentage=40.0,
        )
        assert "Slide 2/5" in update.get_progress_text()

    def test_error_detail_message(self):
        """Detailed errors should include all available context."""
        error = ErrorInfo(
            error_type="ValueError",
            error_message="boom",
            slide_index=3,
            stage=ProcessingStage.FAILED,
            context={"job": "video"},
        )
        text = error.get_detailed_message()
        assert "ValueError: boom" in text
        assert "Slide: 3" in text
        assert "Stage: failed" in text


class TestVideoProgressTracker:
    """Tests for VideoProgressTracker."""

    def test_stage_and_slide_progress_updates(self):
        """Progress updates should record stages and callbacks."""
        tracker = VideoProgressTracker("op-1", total_slides=4)
        seen = []
        tracker.add_progress_callback(seen.append)

        tracker.update_stage(ProcessingStage.VALIDATING, "checking")
        tracker.update_slide_progress(1, ProcessingStage.CREATING_SEGMENTS, "slide two")

        assert tracker.current_stage == ProcessingStage.CREATING_SEGMENTS
        assert tracker.current_slide == 2
        assert len(tracker.progress_history) == 2
        assert len(seen) == 2

    def test_report_error_and_mark_failed(self):
        """Errors and failure state should be tracked."""
        tracker = VideoProgressTracker("op-2", total_slides=1)
        errors = []
        tracker.add_error_callback(errors.append)

        tracker.report_error(RuntimeError("boom"), slide_index=1, context={"phase": "x"})
        tracker.mark_failed(RuntimeError("boom"), slide_index=1)

        status = tracker.get_current_status()
        report = tracker.get_detailed_report()

        assert status["error_count"] >= 1
        assert status["is_completed"] is True
        assert errors
        assert report["error_count"] >= 1
        assert report["progress_updates_count"] >= 1

    def test_stage_updates_ignore_cancelled_trackers_and_callback_errors(self):
        """Cancelled trackers should stop updating, and callback failures should not break progress."""
        tracker = VideoProgressTracker("op-2b", total_slides=3)
        seen = []

        def broken_callback(update):
            raise RuntimeError("callback boom")

        tracker.add_progress_callback(broken_callback)
        tracker.add_progress_callback(seen.append)
        tracker.mark_cancelled({"cleanup": True})
        tracker.update_stage(ProcessingStage.VALIDATING, "ignored")

        assert tracker.current_stage == ProcessingStage.CANCELLED
        assert tracker.progress_history[-1].stage == ProcessingStage.CANCELLED
        assert len(seen) == 1

    def test_stage_update_callback_errors_do_not_break_updates(self):
        """Progress callback failures should be swallowed and still record progress."""
        tracker = VideoProgressTracker("op-2bb", total_slides=3)

        def broken_callback(update):
            raise RuntimeError("callback boom")

        tracker.add_progress_callback(broken_callback)
        tracker.update_stage(ProcessingStage.VALIDATING, "checking")

        assert tracker.current_stage == ProcessingStage.VALIDATING
        assert len(tracker.progress_history) == 1

    def test_slide_progress_ignored_after_cancel(self):
        """Cancelled trackers should ignore slide-specific progress updates too."""
        tracker = VideoProgressTracker("op-2bc", total_slides=3)
        tracker.mark_cancelled({"cleanup": True})
        tracker.update_slide_progress(1, ProcessingStage.CREATING_SEGMENTS, "ignored")

        assert tracker.current_slide == 0
        assert len(tracker.progress_history) == 1

    def test_unknown_stage_maps_to_zero_progress(self):
        """Unknown stages should fall back to zero progress."""
        tracker = VideoProgressTracker("op-2bd", total_slides=3)

        class _Stage:
            value = "custom"

        assert tracker._calculate_stage_progress(_Stage()) == 0

    def test_get_current_status_and_report_include_latest_entries(self):
        """Status snapshots should include latest progress and error details."""
        tracker = VideoProgressTracker("op-2c", total_slides=2)
        tracker.update_stage(ProcessingStage.VALIDATING, "checking")
        tracker.report_error(ValueError("boom"), slide_index=1, context={"step": "validate"})

        status = tracker.get_current_status()
        report = tracker.get_detailed_report()

        assert status["latest_message"] == "checking"
        assert "ValueError: boom" in status["latest_error"]
        assert report["progress_history"][0]["stage"] == "validating"
        assert report["error_history"][0]["error_type"] == "ValueError"

    def test_mark_completed_and_cancelled(self, tmp_path):
        """Completion and cancellation should update final stage."""
        tracker = VideoProgressTracker("op-3", total_slides=2)
        tracker.mark_completed(tmp_path / "out.mp4", file_size=2048, duration=3.5)
        assert tracker.current_stage == ProcessingStage.COMPLETED

        tracker2 = VideoProgressTracker("op-4", total_slides=2)
        tracker2.mark_cancelled({"cleanup": True})
        assert tracker2.current_stage == ProcessingStage.CANCELLED
        assert tracker2.is_cancelled is True


class TestProgressReporter:
    """Tests for console progress reporter."""

    def test_throttles_and_prints(self, capsys):
        """Reporter should print and throttle repeated updates."""
        reporter = ProgressReporter(show_detailed=False)
        reporter.min_update_interval = 999
        update = ProgressUpdate(stage=ProcessingStage.VALIDATING, progress_percentage=10.0)
        reporter.on_progress_update(update)
        reporter.on_progress_update(update)

        captured = capsys.readouterr()
        assert "Validating" in captured.out

    def test_error_and_completion_output(self, capsys):
        """Reporter should print errors and completion summaries."""
        reporter = ProgressReporter(show_detailed=True)
        reporter.last_progress_time = 0
        reporter.on_error(ErrorInfo(error_type="ValueError", error_message="boom"))
        reporter.on_completion({"is_completed": True, "stage": "completed", "elapsed_time_seconds": 1.2})

        captured = capsys.readouterr()
        assert "ERROR:" in captured.out
        assert "completed successfully" in captured.out

    def test_completion_output_for_failed_and_cancelled(self, capsys):
        """Reporter should render failed and cancelled completion states."""
        reporter = ProgressReporter(show_detailed=True)
        reporter.last_progress_time = 0
        reporter.on_completion({"is_completed": True, "stage": "failed", "elapsed_time_seconds": 0.5, "latest_error": "boom"})
        reporter.on_completion({"is_completed": True, "stage": "cancelled", "elapsed_time_seconds": 0.2})

        captured = capsys.readouterr()
        assert "Video synthesis failed!" in captured.out
        assert "Video synthesis cancelled!" in captured.out
