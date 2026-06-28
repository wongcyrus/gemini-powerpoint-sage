"""Tests for the simple video combiner utility."""

from pathlib import Path
from types import SimpleNamespace

import utils.video_combiner as video_combiner


class TestVideoCombiner:
    """Tests for video combination flow."""

    def test_combine_videos_returns_false_when_input_is_missing(self, tmp_path):
        """Missing source videos should fail fast."""
        assert video_combiner.combine_videos([str(tmp_path / "missing.mp4")], str(tmp_path / "out.mp4"), verbose=False) is False

    def test_combine_videos_writes_output_and_closes_clips(self, monkeypatch, tmp_path):
        """Successful combination should write the output and clean up clips."""
        input_1 = tmp_path / "video1.mp4"
        input_2 = tmp_path / "video2.mp4"
        input_1.write_bytes(b"1")
        input_2.write_bytes(b"2")
        output = tmp_path / "combined.mp4"

        closed = []

        class FakeClip:
            def __init__(self, path):
                self.path = path
                self.duration = 1.5
                self.size = (640, 480)

            def close(self):
                closed.append(self.path)

        class FakeFinalClip:
            def write_videofile(self, output_path, codec=None, audio_codec=None, verbose=None, logger=None):
                Path(output_path).write_bytes(b"combined")

            def close(self):
                closed.append("final")

        monkeypatch.setattr(video_combiner, "VideoFileClip", lambda path: FakeClip(path))
        monkeypatch.setattr(video_combiner, "concatenate_videoclips", lambda clips: FakeFinalClip())

        assert video_combiner.combine_videos([str(input_1), str(input_2)], str(output), verbose=False) is True
        assert output.exists()
        assert set(closed) == {str(input_1), str(input_2), "final"}

    def test_combine_videos_returns_false_when_loading_fails(self, monkeypatch, tmp_path):
        """A clip load failure should clean up already-opened clips."""
        input_1 = tmp_path / "video1.mp4"
        input_2 = tmp_path / "video2.mp4"
        input_1.write_bytes(b"1")
        input_2.write_bytes(b"2")

        closed = []

        class FakeClip:
            def __init__(self, path):
                self.path = path

            def close(self):
                closed.append(self.path)

        def fake_video_file_clip(path):
            if path.endswith("video2.mp4"):
                raise RuntimeError("boom")
            return FakeClip(path)

        monkeypatch.setattr(video_combiner, "VideoFileClip", fake_video_file_clip)

        assert video_combiner.combine_videos([str(input_1), str(input_2)], str(tmp_path / "out.mp4"), verbose=False) is False
        assert closed == [str(input_1)]
