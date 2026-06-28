"""Tests for the video synthesis orchestration service."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.domain.video_synthesis import AudioAnalysisError, FileValidationError, VideoConfig, VideoProcessingError, VideoSynthesisError, VideoSynthesisRequest
from services.video_synthesis.video_synthesis_service import VideoSynthesisService


def _make_request(tmp_path: Path) -> VideoSynthesisRequest:
    image = tmp_path / "slide_1.png"
    audio = tmp_path / "slide_1.mp3"
    image.write_bytes(b"img")
    audio.write_bytes(b"aud")
    return VideoSynthesisRequest(
        slide_images=[image],
        audio_files=[audio],
        output_path=tmp_path / "final.mp4",
        config=VideoConfig(),
        presentation_id="deck-1",
    )


class TestVideoSynthesisService:
    """Tests for service orchestration."""

    def test_config_and_format_helpers(self):
        """Simple helper methods should expose config and formats."""
        service = VideoSynthesisService()

        assert service.get_supported_formats()["video_formats"] == ["mp4", "avi", "mkv", "webm"]
        assert service.create_default_config().fps == 30
        assert service.create_optimized_config(10, 2).fade_duration <= 0.5
        assert service.cancel_operation("op-1") == {"cancelled": False, "reason": "Cancellation not implemented"}

    def test_validate_request_and_failure_flow(self, tmp_path):
        """Request validation errors should surface as file validation failures."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        request = _make_request(tmp_path)
        tracker = Mock()

        with patch.object(service.file_validator, "validate_slide_audio_pairs", side_effect=FileValidationError("bad pair")), patch.object(
            service.file_validator, "validate_output_path"
        ), patch.object(service.config_manager, "validate_config"):
            with pytest.raises(FileValidationError, match="Request validation failed"):
                service._validate_request(request, tracker)

        tracker.report_error.assert_called_once()

    def test_analyze_audio_files_success_and_failure(self, tmp_path):
        """Audio analysis should build segments and report failures."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        request = _make_request(tmp_path)
        tracker = Mock()

        with patch.object(service, "_extract_slide_number_from_files", return_value=1), patch(
            "core.domain.video_synthesis.SlideVideoSegment.from_files"
        ) as mock_from_files:
            mock_segment = Mock(duration_seconds=2.5)
            mock_from_files.return_value = mock_segment
            segments = service._analyze_audio_files(request, tracker)

        assert segments == [mock_segment]
        tracker.update_slide_progress.assert_called_once()

        with patch.object(service, "_extract_slide_number_from_files", side_effect=ValueError("boom")):
            with pytest.raises(AudioAnalysisError, match="Failed to analyze audio"):
                service._analyze_audio_files(request, tracker)

    def test_create_and_finalize_paths(self, tmp_path):
        """Segment creation, concatenation, and finalization should stitch together."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        request = _make_request(tmp_path)
        tracker = Mock()
        segments = [Mock(image_path=request.slide_images[0], duration_seconds=1.0, temp_video_path=None)]

        fake_manager = Mock()
        fake_manager.create_segment_temp_dir.return_value = tmp_path / "segments"
        fake_manager.create_working_temp_dir.return_value = tmp_path / "work"
        fake_manager.get_temp_file_path.return_value = tmp_path / "work" / "concatenated.mp4"
        fake_manager.move_to_output.return_value = request.output_path

        fake_processor = Mock()
        fake_processor.create_video_segment.return_value = tmp_path / "segments" / "segment_001.mp4"
        fake_processor.concatenate_segments.return_value = tmp_path / "work" / "concatenated.mp4"

        with patch("services.video_synthesis.video_synthesis_service.FFmpegVideoProcessor", return_value=fake_processor):
            processed = service._create_video_segments(segments, request.config, fake_manager, tracker)
            merged = service._concatenate_segments(processed, request.config, fake_manager, tracker)
            final = service._finalize_output(merged, request.output_path, fake_manager, tracker)

        assert final == request.output_path
        assert processed[0].temp_video_path.name == "segment_001.mp4"
        assert merged.name == "concatenated.mp4"

    def test_synthesize_video_success_and_failure(self, tmp_path):
        """The top-level synthesize flow should return success or failure results."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        request = _make_request(tmp_path)
        temp_output = tmp_path / "temp.mp4"
        temp_output.write_bytes(b"video")
        request.output_path.write_bytes(b"final")
        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        fake_manager = Mock()
        fake_manager.temp_dir = tmp_path
        fake_manager.cleanup.return_value = {"files_removed": 1}

        fake_segment = Mock(duration_seconds=2.0, temp_video_path=temp_output, image_path=request.slide_images[0])

        with patch("services.video_synthesis.video_synthesis_service.VideoFileManager", return_value=fake_manager), patch.object(
            service, "_check_disk_space"
        ), patch.object(service, "_validate_request"), patch.object(
            service, "_analyze_audio_files", return_value=[fake_segment]
        ), patch.object(
            service, "_create_video_segments", return_value=[fake_segment]
        ), patch.object(
            service, "_concatenate_segments", return_value=temp_output
        ), patch.object(
            service, "_finalize_output", return_value=request.output_path
        ), patch(
            "services.video_synthesis.video_synthesis_service.FFmpegVideoProcessor"
        ) as mock_ffmpeg_processor:
            mock_ffmpeg_processor.return_value.get_video_info.return_value = {
                "duration_seconds": 2.0,
                "size": 123,
            }
            result = service.synthesize_video(request)

        assert result.success is True
        assert result.output_path == request.output_path
        assert result.metadata["config_summary"]["output_format"] == "MP4"

        with patch("services.video_synthesis.video_synthesis_service.VideoFileManager", return_value=fake_manager), patch.object(
            service, "_check_disk_space"
        ), patch.object(service, "_validate_request", side_effect=FileValidationError("bad request")):
            failed = service.synthesize_video(request)

        assert failed.success is False
        assert "bad request" in failed.error_message

    def test_synthesize_video_uses_fallback_video_info_and_completion_timeout(self, tmp_path):
        """Video synthesis should still succeed when video info and completion hooks fail."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        request = _make_request(tmp_path)
        request.output_path.write_bytes(b"final")

        fake_manager = Mock()
        fake_manager.temp_dir = tmp_path
        fake_manager.cleanup.return_value = {"files_removed": 1}

        fake_segment = Mock(duration_seconds=2.0, temp_video_path=request.output_path, image_path=request.slide_images[0])

        with patch("services.video_synthesis.video_synthesis_service.VideoFileManager", return_value=fake_manager), patch.object(
            service, "_check_disk_space"
        ), patch.object(service, "_validate_request"), patch.object(
            service, "_analyze_audio_files", return_value=[fake_segment]
        ), patch.object(
            service, "_create_video_segments", return_value=[fake_segment]
        ), patch.object(
            service, "_concatenate_segments", return_value=request.output_path
        ), patch.object(
            service,
            "_finalize_output",
            side_effect=lambda temp_output, final_output_path, file_manager, progress_tracker: (
                final_output_path.write_bytes(b"video"),
                final_output_path,
            )[1],
        ), patch(
            "services.video_synthesis.video_synthesis_service.FFmpegVideoProcessor"
        ) as mock_ffmpeg_processor, patch(
            "services.video_synthesis.video_synthesis_service.VideoProgressTracker.mark_completed",
            side_effect=TimeoutError("boom"),
        ):
            mock_ffmpeg_processor.return_value.get_video_info.side_effect = RuntimeError("info failed")
            result = service.synthesize_video(request)

        assert result.success is True
        assert result.metadata["video_info"]["estimated"] is True
        assert result.duration_seconds == 2.0

    def test_synthesize_video_failure_after_segment_creation(self, tmp_path):
        """Later-stage failures should return failure results and clean up temp files."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        request = _make_request(tmp_path)
        request.output_path.write_bytes(b"final")

        fake_manager = Mock()
        fake_manager.temp_dir = tmp_path
        fake_manager.cleanup.return_value = {"files_removed": 2}

        fake_segment = Mock(duration_seconds=2.0, temp_video_path=request.output_path, image_path=request.slide_images[0])

        with patch("services.video_synthesis.video_synthesis_service.VideoFileManager", return_value=fake_manager), patch.object(
            service, "_check_disk_space"
        ), patch.object(service, "_validate_request"), patch.object(
            service, "_analyze_audio_files", return_value=[fake_segment]
        ), patch.object(
            service, "_create_video_segments", return_value=[fake_segment]
        ), patch.object(
            service, "_concatenate_segments", side_effect=VideoProcessingError("concat failed")
        ):
            result = service.synthesize_video(request)

        assert result.success is False
        assert "concat failed" in result.error_message
        fake_manager.cleanup.assert_called()

    def test_combine_videos(self, tmp_path):
        """Video combination should analyze inputs and write the final output."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        video1 = tmp_path / "a.mp4"
        video2 = tmp_path / "b.mp4"
        video1.write_bytes(b"1")
        video2.write_bytes(b"2")
        output = tmp_path / "combined.mp4"

        def fake_run(cmd, capture_output, text, timeout):
            if "ffprobe" in cmd:
                return Mock(returncode=0, stdout="1.0")
            output.write_bytes(b"combined")
            return Mock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            result = service.combine_videos([video1, video2], output)

        assert result.success is True
        assert result.output_path == output
        assert output.exists()

    def test_check_disk_space_raises_for_low_capacity(self, tmp_path):
        """Insufficient disk space should fail fast."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        request = _make_request(tmp_path)

        class _Stat:
            f_frsize = 1
            f_bavail = 1024 * 1024 * 1024

        with patch("os.statvfs", return_value=_Stat()):
            with pytest.raises(VideoSynthesisError, match="Insufficient disk space"):
                service._check_disk_space(request, Mock(temp_dir=tmp_path))

    def test_check_disk_space_handles_large_presentations_without_error(self, tmp_path):
        """Large presentations should take the conservative branch without failing."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        image = tmp_path / "slide_1.png"
        audio = tmp_path / "slide_1.mp3"
        image.write_bytes(b"img")
        audio.write_bytes(b"aud")
        request = VideoSynthesisRequest(
            slide_images=[image] * 201,
            audio_files=[audio] * 201,
            output_path=tmp_path / "final.mp4",
            config=VideoConfig(),
            presentation_id="deck-1",
        )

        class _Stat:
            f_frsize = 1
            f_bavail = 10 * 1024 * 1024 * 1024

        with patch("os.statvfs", return_value=_Stat()):
            service._check_disk_space(request, Mock(temp_dir=tmp_path))

    def test_create_video_segments_uses_chunked_processing_and_mini_cleanup(self, tmp_path):
        """Chunked processing should call the mini cleanup between chunks."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        tracker = Mock()
        file_manager = Mock()
        file_manager.create_segment_temp_dir.return_value = tmp_path / "segments"
        file_manager._cleanup_temp_files_immediately = Mock()

        segments = []
        for idx in range(3):
            image = tmp_path / f"slide_{idx + 1}.png"
            audio = tmp_path / f"slide_{idx + 1}.mp3"
            image.write_bytes(b"img")
            audio.write_bytes(b"aud")
            segments.append(Mock(image_path=image, duration_seconds=1.0, temp_video_path=None))

        fake_ffmpeg = Mock()
        fake_ffmpeg.create_video_segment.side_effect = [
            tmp_path / "segments" / "segment_001.mp4",
            tmp_path / "segments" / "segment_002.mp4",
            tmp_path / "segments" / "segment_003.mp4",
        ]

        with patch("services.video_synthesis.video_synthesis_service.CleanupConfig.should_use_chunked_processing", return_value=True), patch(
            "services.video_synthesis.video_synthesis_service.CleanupConfig.get_chunk_size", return_value=1
        ), patch(
            "services.video_synthesis.video_synthesis_service.FFmpegVideoProcessor", return_value=fake_ffmpeg
        ):
            processed = service._create_video_segments(segments, VideoConfig(), file_manager, tracker)

        assert len(processed) == 3
        assert file_manager._cleanup_temp_files_immediately.call_count == 2
        assert tracker.update_slide_progress.call_count == 3

    def test_concatenate_segments_and_finalize_output(self, tmp_path):
        """Concatenation and finalization should wire through the processor and file manager."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        tracker = Mock()
        file_manager = Mock()
        file_manager.create_working_temp_dir.return_value = tmp_path / "work"
        file_manager.get_temp_file_path.return_value = tmp_path / "work" / "concatenated.mp4"
        file_manager.move_to_output.return_value = tmp_path / "final.mp4"

        segment_path = tmp_path / "segment_001.mp4"
        segment_path.write_bytes(b"segment")
        image = tmp_path / "slide.png"
        audio = tmp_path / "audio.mp3"
        image.write_bytes(b"img")
        audio.write_bytes(b"aud")
        segment = Mock(image_path=image, temp_video_path=segment_path)

        fake_ffmpeg = Mock()
        fake_ffmpeg.concatenate_segments.return_value = tmp_path / "work" / "concatenated.mp4"

        with patch("services.video_synthesis.video_synthesis_service.FFmpegVideoProcessor", return_value=fake_ffmpeg):
            temp_output = service._concatenate_segments([segment], VideoConfig(), file_manager, tracker)
            final_output = service._finalize_output(temp_output, tmp_path / "final.mp4", file_manager, tracker)

        assert temp_output.name == "concatenated.mp4"
        assert final_output == tmp_path / "final.mp4"

    def test_combine_videos_failure_returns_failure_result(self, tmp_path):
        """FFmpeg combine failures should be converted into failure results."""
        service = VideoSynthesisService(temp_dir=tmp_path)
        video1 = tmp_path / "a.mp4"
        video2 = tmp_path / "b.mp4"
        video1.write_bytes(b"1")
        video2.write_bytes(b"2")
        output = tmp_path / "combined.mp4"

        def fake_run(cmd, capture_output, text, timeout):
            if "ffprobe" in cmd:
                return Mock(returncode=0, stdout="1.0")
            return Mock(returncode=1, stdout="", stderr="boom")

        with patch("subprocess.run", side_effect=fake_run):
            result = service.combine_videos([video1, video2], output)

        assert result.success is False
        assert "boom" in result.error_message
