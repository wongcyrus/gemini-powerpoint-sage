"""Tests for file validation helpers used by video synthesis."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from core.domain.video_synthesis import FileValidationError
from services.video_synthesis.file_validator import FileValidator


class TestFileValidator:
    """Tests for FileValidator."""

    def test_validate_image_file_returns_metadata(self, tmp_path):
        """Valid images should return metadata."""
        image_path = tmp_path / "slide_1.png"
        Image.new("RGB", (640, 360), "white").save(image_path)

        metadata = FileValidator().validate_image_file(image_path)

        assert metadata["width"] == 640
        assert metadata["height"] == 360
        assert metadata["file_extension"] == ".png"

    def test_validate_image_file_rejects_missing(self, tmp_path):
        """Missing image files should fail."""
        with pytest.raises(FileValidationError, match="Image file not found"):
            FileValidator().validate_image_file(tmp_path / "missing.png")

    def test_validate_image_file_rejects_bad_format(self, tmp_path):
        """Unsupported image formats should fail."""
        bad_file = tmp_path / "slide_1.gif"
        bad_file.write_bytes(b"gif")

        with pytest.raises(FileValidationError, match="Unsupported image format"):
            FileValidator().validate_image_file(bad_file)

    def test_validate_image_file_rejects_corrupted_image(self, tmp_path):
        """Corrupted image files should fail validation."""
        bad_file = tmp_path / "slide_1.png"
        bad_file.write_bytes(b"not-an-image")

        with pytest.raises(FileValidationError, match="Invalid or corrupted image file"):
            FileValidator().validate_image_file(bad_file)

    def test_validate_image_file_rejects_invalid_dimensions(self, tmp_path, monkeypatch):
        """Images with zero dimensions should be rejected."""
        image_path = tmp_path / "slide_1.png"
        image_path.write_bytes(b"img")

        class _Image:
            size = (0, 10)
            mode = "RGB"
            format = "PNG"

            def verify(self):
                return None

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        monkeypatch.setattr("services.video_synthesis.file_validator.Image.open", lambda _path: _Image())

        with pytest.raises(FileValidationError, match="Invalid image dimensions"):
            FileValidator().validate_image_file(image_path)

    def test_validate_audio_file_returns_metadata(self, tmp_path):
        """Valid audio files should return metadata from ffprobe."""
        audio_path = tmp_path / "slide_1.mp3"
        audio_path.write_bytes(b"mp3")
        result = Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "streams": [
                        {"codec_type": "audio", "codec_name": "aac", "sample_rate": "44100", "channels": 2}
                    ],
                    "format": {
                        "duration": "2.5",
                        "size": "1234",
                        "format_name": "mp3",
                        "bit_rate": "128000",
                    },
                }
            ),
        )

        with patch("services.video_synthesis.file_validator.subprocess.run", return_value=result):
            metadata = FileValidator().validate_audio_file(audio_path)

        assert metadata["duration_seconds"] == 2.5
        assert metadata["codec_name"] == "aac"
        assert metadata["channels"] == 2

    def test_validate_audio_file_requires_audio_stream(self, tmp_path):
        """Files without an audio stream should fail."""
        audio_path = tmp_path / "slide_1.mp3"
        audio_path.write_bytes(b"mp3")
        result = Mock(returncode=0, stdout=json.dumps({"streams": [], "format": {"duration": "2.5"}}))

        with patch("services.video_synthesis.file_validator.subprocess.run", return_value=result):
            with pytest.raises(FileValidationError, match="No audio stream found"):
                FileValidator().validate_audio_file(audio_path)

    def test_validate_audio_file_rejects_bad_extension_and_bad_probe(self, tmp_path):
        """Bad extensions and probe failures should be rejected."""
        audio_path = tmp_path / "slide_1.wav"
        audio_path.write_bytes(b"wav")

        with pytest.raises(FileValidationError, match="Unsupported audio format"):
            FileValidator().validate_audio_file(audio_path)

        audio_path = tmp_path / "slide_2.mp3"
        audio_path.write_bytes(b"mp3")
        with patch("services.video_synthesis.file_validator.subprocess.run", return_value=Mock(returncode=1, stderr="boom")):
            with pytest.raises(FileValidationError, match="FFprobe failed"):
                FileValidator().validate_audio_file(audio_path)

        with patch(
            "services.video_synthesis.file_validator.subprocess.run",
            side_effect=FileNotFoundError("ffprobe missing"),
        ):
            with pytest.raises(FileValidationError, match="FFprobe not found"):
                FileValidator().validate_audio_file(audio_path)

        with patch(
            "services.video_synthesis.file_validator.subprocess.run",
            side_effect=json.JSONDecodeError("bad", "{}", 0),
        ):
            with pytest.raises(FileValidationError, match="Failed to parse FFprobe output"):
                FileValidator().validate_audio_file(audio_path)

    def test_validate_slide_audio_pairs(self, tmp_path):
        """Pair validation should combine image and audio metadata."""
        image_path = tmp_path / "slide_1.png"
        audio_path = tmp_path / "slide_1.mp3"
        Image.new("RGB", (10, 10), "white").save(image_path)
        audio_path.write_bytes(b"mp3")

        validator = FileValidator()
        with patch.object(validator, "validate_audio_file", return_value={"duration_seconds": 1.0}):
            pairs = validator.validate_slide_audio_pairs([image_path], [audio_path])

        assert len(pairs) == 1
        assert pairs[0][0]["width"] == 10

    def test_validate_slide_audio_pairs_rejects_empty(self):
        """Empty input should fail early."""
        with pytest.raises(FileValidationError, match="At least one slide-audio pair"):
            FileValidator().validate_slide_audio_pairs([], [])

    def test_validate_slide_audio_pairs_wraps_pair_errors(self, tmp_path):
        """Pair validation should annotate failing pair numbers."""
        image_path = tmp_path / "slide_1.png"
        audio_path = tmp_path / "slide_1.mp3"
        Image.new("RGB", (10, 10), "white").save(image_path)
        audio_path.write_bytes(b"mp3")

        validator = FileValidator()
        with patch.object(validator, "validate_image_file", side_effect=FileValidationError("bad image")):
            with pytest.raises(FileValidationError, match="Validation failed for pair 1"):
                validator.validate_slide_audio_pairs([image_path], [audio_path])

    def test_validate_slide_audio_pairs_rejects_mismatched_counts(self, tmp_path):
        """Count mismatches should fail early."""
        with pytest.raises(FileValidationError, match="must match"):
            FileValidator().validate_slide_audio_pairs([tmp_path / "a.png"], [])

    def test_unsupported_and_output_path_helpers(self, tmp_path):
        """Unsupported-file detection and output validation should be deterministic."""
        validator = FileValidator()
        image = tmp_path / "bad.gif"
        audio = tmp_path / "bad.wav"
        unknown = tmp_path / "missing.xyz"
        image.write_bytes(b"gif")
        audio.write_bytes(b"wav")

        unsupported = validator.get_unsupported_files([image, audio, unknown])
        message = validator.generate_format_error_message(unsupported)

        assert image in unsupported["unsupported_images"]
        assert audio in unsupported["unsupported_audio"]
        assert "Unsupported image formats" in message
        assert "Unsupported audio formats" in message

        output = tmp_path / "nested" / "video.mp4"
        validator.validate_output_path(output)
        assert output.parent.exists()

    def test_get_unsupported_files_and_generate_message_handles_empty(self, tmp_path):
        """Unsupported-file helper should classify missing, image, audio, and unknown paths."""
        validator = FileValidator()
        image = tmp_path / "bad.bmp"
        audio = tmp_path / "bad.flac"
        unknown = tmp_path / "missing.xyz"
        image.write_bytes(b"bmp")
        audio.write_bytes(b"flac")

        unsupported = validator.get_unsupported_files([image, audio, unknown])
        message = validator.generate_format_error_message({"unsupported_images": [], "unsupported_audio": [], "unknown": []})

        assert image in unsupported["unsupported_images"]
        assert audio in unsupported["unsupported_audio"]
        assert unknown in unsupported["unknown"]
        assert message == ""

    def test_validate_output_path_rejects_bad_extension_and_non_writable(self, tmp_path, monkeypatch):
        """Output validation should reject bad extensions and unwritable dirs."""
        validator = FileValidator()
        bad_ext = tmp_path / "nested" / "video.txt"

        with pytest.raises(FileValidationError, match="Unsupported output video format"):
            validator.validate_output_path(bad_ext)

        good = tmp_path / "nested2" / "video.mp4"
        monkeypatch.setattr("services.video_synthesis.file_validator.os.access", lambda path, mode: False)
        with pytest.raises(FileValidationError, match="Output directory is not writable"):
            validator.validate_output_path(good)
