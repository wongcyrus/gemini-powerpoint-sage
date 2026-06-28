"""Tests for natural file sorting helpers."""

from pathlib import Path

import pytest

from utils.file_sorting import (
    extract_slide_number,
    natural_sort_files,
    natural_sort_key,
    pair_slide_audio_files,
    verify_slide_audio_pairing,
)


class TestFileSorting:
    """Tests for file sorting and pairing."""

    def test_natural_sort_key_orders_numbers_naturally(self):
        """Natural sort keys should compare numeric segments as numbers."""
        files = ["slide_10.png", "slide_2.png", "slide_1.png"]

        assert sorted(files, key=natural_sort_key) == [
            "slide_1.png",
            "slide_2.png",
            "slide_10.png",
        ]

    def test_natural_sort_files_sorts_path_objects(self):
        """Path objects should be sorted by filename in natural order."""
        files = [Path("slide_12.png"), Path("slide_3.png"), Path("slide_1.png")]

        assert natural_sort_files(files) == [
            Path("slide_1.png"),
            Path("slide_3.png"),
            Path("slide_12.png"),
        ]

    def test_pair_slide_audio_files_matches_sorted_pairs(self):
        """Slides and audio files should be zipped after natural sorting."""
        slides = [Path("slide_2.png"), Path("slide_1.png")]
        audio = [Path("slide_2_hash.mp3"), Path("slide_1_hash.mp3")]

        paired = pair_slide_audio_files(slides, audio)

        assert paired == [
            (Path("slide_1.png"), Path("slide_1_hash.mp3")),
            (Path("slide_2.png"), Path("slide_2_hash.mp3")),
        ]

    def test_pair_slide_audio_files_rejects_mismatched_lengths(self):
        """Pairing should fail if slide and audio counts differ."""
        with pytest.raises(ValueError, match="must match"):
            pair_slide_audio_files([Path("slide_1.png")], [])

    def test_extract_slide_number_prefers_slide_prefix(self):
        """Slide numbers should be extracted from slide-prefixed filenames first."""
        assert extract_slide_number("slide_10_reimagined.png") == 10
        assert extract_slide_number("audio_5.mp3") == 5

    def test_extract_slide_number_raises_when_missing(self):
        """Filenames without digits should fail validation."""
        with pytest.raises(ValueError, match="No slide number found"):
            extract_slide_number("intro.png")

    def test_verify_slide_audio_pairing_checks_slide_numbers(self):
        """Pair verification should catch mismatched slide numbering."""
        good = verify_slide_audio_pairing(
            [Path("slide_1.png"), Path("slide_2.png")],
            [Path("slide_1_hash.mp3"), Path("slide_2_hash.mp3")],
        )
        bad = verify_slide_audio_pairing(
            [Path("slide_1.png")],
            [Path("slide_2_hash.mp3")],
        )

        assert good is True
        assert bad is False
