"""Tests for audio analysis helpers used by video synthesis."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.domain.video_synthesis import AudioAnalysisError
from services.video_synthesis import audio_analyzer as audio_module
from services.video_synthesis.audio_analyzer import AudioAnalyzer


class TestAudioAnalyzer:
    """Tests for AudioAnalyzer."""

    def test_get_audio_duration_success(self, tmp_path):
        """Duration extraction should parse ffmpeg probe output."""
        audio_path = tmp_path / "slide_1.mp3"
        audio_path.write_bytes(b"mp3")
        probe = {"format": {"duration": "2.75"}}

        with patch.object(audio_module, "FFMPEG_AVAILABLE", True), patch.object(audio_module, "ffmpeg") as mock_ffmpeg:
            mock_ffmpeg.probe.return_value = probe
            duration = AudioAnalyzer().get_audio_duration(audio_path)

        assert duration == 2.75
        mock_ffmpeg.probe.assert_called_once_with(str(audio_path))

    def test_get_audio_duration_rejects_missing_ffmpeg(self, tmp_path):
        """Missing ffmpeg support should fail clearly."""
        audio_path = tmp_path / "slide_1.mp3"
        audio_path.write_bytes(b"mp3")

        with patch.object(audio_module, "FFMPEG_AVAILABLE", False):
            with pytest.raises(AudioAnalysisError, match="not available"):
                AudioAnalyzer().get_audio_duration(audio_path)

    def test_get_audio_metadata_and_validation(self, tmp_path):
        """Metadata extraction and validation should use probe data."""
        audio_path = tmp_path / "slide_1.mp3"
        audio_path.write_bytes(b"mp3")
        probe = {
            "format": {
                "duration": "4.5",
                "size": "321",
                "format_name": "mp3",
                "bit_rate": "128000",
                "tags": {"artist": "test"},
            },
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100",
                    "channels": 2,
                    "channel_layout": "stereo",
                }
            ],
        }

        with patch.object(audio_module, "FFMPEG_AVAILABLE", True), patch.object(audio_module, "ffmpeg") as mock_ffmpeg:
            mock_ffmpeg.probe.return_value = probe
            analyzer = AudioAnalyzer()

            metadata = analyzer.get_audio_metadata(audio_path)
            assert analyzer.validate_audio_file(audio_path) is True
            assert analyzer.get_total_duration([audio_path]) == 4.5

        assert metadata["codec_name"] == "mp3"
        assert metadata["tags"]["artist"] == "test"

    def test_batch_analyze_audio_files(self, tmp_path):
        """Batch analysis should aggregate per-file metadata."""
        audio_path = tmp_path / "slide_1.mp3"
        audio_path.write_bytes(b"mp3")
        probe = {"format": {"duration": "1.25", "size": "10", "format_name": "mp3", "bit_rate": "128000"}, "streams": [{"codec_type": "audio", "codec_name": "mp3", "sample_rate": "44100", "channels": 2}]}

        with patch.object(audio_module, "FFMPEG_AVAILABLE", True), patch.object(audio_module, "ffmpeg") as mock_ffmpeg:
            mock_ffmpeg.probe.return_value = probe
            results = AudioAnalyzer().batch_analyze_audio_files([audio_path])

        assert results[audio_path]["duration_seconds"] == 1.25
