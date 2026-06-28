"""Tests for the MoviePy video processor."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from core.domain.video_synthesis import SlideVideoSegment, VideoConfig
from services.video_synthesis.moviepy_processor import MoviePyVideoProcessor


class _FakeClip:
    def __init__(self, size=(640, 360), duration=2.0):
        self.size = size
        self.duration = duration
        self.closed = False

    def with_duration(self, duration):
        self.duration = duration
        return self

    def resized(self, new_size):
        self.size = new_size
        return self

    def with_position(self, _position):
        return self

    def with_fps(self, _fps):
        return self

    def with_audio(self, _audio):
        return self

    def with_effects(self, _effects):
        return self

    def write_videofile(self, output_path, fps=None, **kwargs):
        Path(output_path).write_bytes(b"video")

    def close(self):
        self.closed = True


class TestMoviePyVideoProcessor:
    """Tests for video segment generation."""

    def test_create_video_segment_uses_cache_hit(self, tmp_path):
        image = tmp_path / "slide_1.png"
        audio = tmp_path / "slide_1.mp3"
        cached = tmp_path / "cached.mp4"
        image.write_bytes(b"image")
        audio.write_bytes(b"audio")
        cached.write_bytes(b"cached")

        segment = SlideVideoSegment(slide_index=1, image_path=image, audio_path=audio, duration_seconds=1.0)
        config = VideoConfig()
        file_manager = Mock(enable_cache=True)
        file_manager.generate_segment_cache_key.return_value = "key"
        file_manager.get_cached_segment.return_value = cached

        work_dir = tmp_path / "work"
        work_dir.mkdir()
        processor = MoviePyVideoProcessor(temp_dir=work_dir)

        result = processor.create_video_segment(segment, config, work_dir, file_manager=file_manager)

        assert result.exists()
        assert segment.temp_video_path == result
        file_manager.cache_segment.assert_not_called()

    def test_create_video_segment_generates_video(self, tmp_path, monkeypatch):
        image = tmp_path / "slide_1.png"
        audio = tmp_path / "slide_1.mp3"
        image.write_bytes(b"image")
        audio.write_bytes(b"audio")

        segment = SlideVideoSegment(slide_index=1, image_path=image, audio_path=audio, duration_seconds=1.0)
        config = VideoConfig(fade_duration=0.0)
        file_manager = Mock(enable_cache=False)
        work_dir = tmp_path / "work"

        audio_clip = _FakeClip(duration=1.5)
        image_clip = _FakeClip(size=(4000, 3000))
        background_clip = _FakeClip(size=config.resolution, duration=1.5)
        composite_clip = _FakeClip(size=config.resolution, duration=1.5)

        monkeypatch.setattr(
            "services.video_synthesis.moviepy_processor.AudioFileClip",
            lambda _path: audio_clip,
        )
        monkeypatch.setattr(
            "services.video_synthesis.moviepy_processor.ImageClip",
            lambda _path: image_clip,
        )
        monkeypatch.setattr(
            "services.video_synthesis.moviepy_processor.ColorClip",
            lambda **kwargs: background_clip,
        )
        monkeypatch.setattr(
            "services.video_synthesis.moviepy_processor.CompositeVideoClip",
            lambda clips: composite_clip,
        )

        processor = MoviePyVideoProcessor(temp_dir=work_dir)

        result = processor.create_video_segment(segment, config, work_dir, file_manager=file_manager)

        assert result.exists()
        assert segment.temp_video_path == result
        assert audio_clip.closed is True
        assert image_clip.closed is True
        assert composite_clip.closed is True

    def test_create_video_segment_uses_fade_effects_without_background(self, tmp_path, monkeypatch):
        image = tmp_path / "slide_1.png"
        audio = tmp_path / "slide_1.mp3"
        image.write_bytes(b"image")
        audio.write_bytes(b"audio")

        segment = SlideVideoSegment(slide_index=1, image_path=image, audio_path=audio, duration_seconds=1.0)
        config = VideoConfig(fade_duration=1.0)
        file_manager = Mock(enable_cache=False)
        work_dir = tmp_path / "work"

        audio_clip = _FakeClip(duration=1.5)
        image_clip = _FakeClip(size=(1280, 720))

        monkeypatch.setattr("services.video_synthesis.moviepy_processor.AudioFileClip", lambda _path: audio_clip)
        monkeypatch.setattr("services.video_synthesis.moviepy_processor.ImageClip", lambda _path: image_clip)
        monkeypatch.setattr("services.video_synthesis.moviepy_processor.ColorClip", lambda **kwargs: _FakeClip())

        processor = MoviePyVideoProcessor(temp_dir=work_dir)

        result = processor.create_video_segment(segment, config, work_dir, file_manager=file_manager)

        assert result.exists()
        assert image_clip.size == (1920, 1080)
        assert audio_clip.closed is True

    def test_create_video_segment_cached_read_failure_falls_through(self, tmp_path, monkeypatch):
        image = tmp_path / "slide_1.png"
        audio = tmp_path / "slide_1.mp3"
        cached = tmp_path / "cached.mp4"
        image.write_bytes(b"image")
        audio.write_bytes(b"audio")
        cached.write_bytes(b"cached")

        segment = SlideVideoSegment(slide_index=1, image_path=image, audio_path=audio, duration_seconds=1.0)
        config = VideoConfig()
        file_manager = Mock(enable_cache=True)
        file_manager.generate_segment_cache_key.return_value = "key"
        file_manager.get_cached_segment.return_value = cached

        work_dir = tmp_path / "work"
        work_dir.mkdir()
        processor = MoviePyVideoProcessor(temp_dir=work_dir)

        monkeypatch.setattr("builtins.open", Mock(side_effect=OSError("boom")))
        monkeypatch.setattr("services.video_synthesis.moviepy_processor.AudioFileClip", lambda _path: _FakeClip(duration=1.0))
        monkeypatch.setattr("services.video_synthesis.moviepy_processor.ImageClip", lambda _path: _FakeClip(size=(1280, 720)))
        monkeypatch.setattr("services.video_synthesis.moviepy_processor.ColorClip", lambda **kwargs: _FakeClip())

        with pytest.raises(Exception):
            processor.create_video_segment(segment, config, work_dir, file_manager=file_manager)

    def test_concatenate_segments_raises_on_empty_input(self, tmp_path):
        processor = MoviePyVideoProcessor(temp_dir=tmp_path)

        with pytest.raises(Exception):
            processor.concatenate_segments([], VideoConfig(), tmp_path / "out.mp4", tmp_path)

    def test_concatenate_segments_writes_single_segment(self, tmp_path, monkeypatch):
        segment_path = tmp_path / "segment_001.mp4"
        segment_path.write_bytes(b"segment")
        image_path = tmp_path / "slide.png"
        audio_path = tmp_path / "audio.mp3"
        image_path.write_bytes(b"image")
        audio_path.write_bytes(b"audio")
        segment = SlideVideoSegment(slide_index=1, image_path=image_path, audio_path=audio_path, duration_seconds=1.0)
        segment.temp_video_path = segment_path

        processor = MoviePyVideoProcessor(temp_dir=tmp_path)
        output_path = tmp_path / "final.mp4"

        monkeypatch.setattr(
            "services.video_synthesis.moviepy_processor.VideoFileClip",
            lambda _path: _FakeClip(duration=1.0),
        )

        result = processor.concatenate_segments([segment], VideoConfig(), output_path, tmp_path)

        assert result == output_path
        assert output_path.exists()

    def test_concatenate_segments_raises_when_output_not_written(self, tmp_path, monkeypatch):
        segment_path = tmp_path / "segment_001.mp4"
        segment_path.write_bytes(b"segment")
        image_path = tmp_path / "slide.png"
        audio_path = tmp_path / "audio.mp3"
        image_path.write_bytes(b"image")
        audio_path.write_bytes(b"audio")
        segment = SlideVideoSegment(slide_index=1, image_path=image_path, audio_path=audio_path, duration_seconds=1.0)
        segment.temp_video_path = segment_path

        class _NoWriteClip(_FakeClip):
            def write_videofile(self, output_path, fps=None, **kwargs):
                return None

        processor = MoviePyVideoProcessor(temp_dir=tmp_path)
        output_path = tmp_path / "final.mp4"

        monkeypatch.setattr(
            "services.video_synthesis.moviepy_processor.VideoFileClip",
            lambda _path: _NoWriteClip(duration=1.0),
        )

        with pytest.raises(Exception):
            processor.concatenate_segments([segment], VideoConfig(), output_path, tmp_path)

    def test_concatenate_with_crossfade_uses_all_clip_positions(self, monkeypatch):
        processor = MoviePyVideoProcessor.__new__(MoviePyVideoProcessor)

        clips = [_FakeClip(duration=4.0), _FakeClip(duration=6.0), _FakeClip(duration=5.0)]
        concatenated = _FakeClip(duration=10.0)

        monkeypatch.setattr(
            "services.video_synthesis.moviepy_processor.concatenate_videoclips",
            lambda processed_clips, padding=None, method=None: concatenated,
        )

        result = processor._concatenate_with_crossfade(clips, 2.0)

        assert result == concatenated

    def test_concatenate_with_crossfade_falls_back_to_simple_concat(self, monkeypatch):
        processor = MoviePyVideoProcessor.__new__(MoviePyVideoProcessor)
        clips = [_FakeClip(duration=4.0), _FakeClip(duration=6.0)]
        concatenated = _FakeClip(duration=10.0)

        monkeypatch.setattr(
            "services.video_synthesis.moviepy_processor.concatenate_videoclips",
            Mock(side_effect=[RuntimeError("boom"), concatenated]),
        )

        result = processor._concatenate_with_crossfade(clips, 2.0)

        assert result == concatenated

    def test_get_video_info_handles_audio_and_no_audio(self, tmp_path, monkeypatch):
        processor = MoviePyVideoProcessor(temp_dir=tmp_path)
        video = tmp_path / "video.mp4"
        video.write_bytes(b"video")

        class _Audio:
            fps = 44100

        class _Clip:
            duration = 3.2
            w = 1920
            h = 1080
            fps = 30
            audio = _Audio()

            def close(self):
                return None

        monkeypatch.setattr("services.video_synthesis.moviepy_processor.VideoFileClip", lambda _path: _Clip())
        info = processor.get_video_info(video)

        assert info["has_audio"] is True
        assert info["audio_fps"] == 44100

        class _ClipNoAudio(_Clip):
            audio = None

        monkeypatch.setattr("services.video_synthesis.moviepy_processor.VideoFileClip", lambda _path: _ClipNoAudio())
        info = processor.get_video_info(video)

        assert info["has_audio"] is False
