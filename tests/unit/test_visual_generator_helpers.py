"""Tests for visual generation helper functions."""

from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from services.visual_generator_helpers import (
    cleanup_reduced_image_file,
    apply_slide_notes,
    build_designer_prompt,
    build_fallback_prompt,
    compute_image_placement_inches,
    get_logo_instruction,
    optimize_image_file,
)


class TestVisualGeneratorHelpers:
    """Tests for pure visual generation helpers."""

    def test_get_logo_instruction_matches_slide_position(self):
        """Slide 1 should request branding, later slides should not."""
        assert "logo/branding" in get_logo_instruction(1)
        assert "DO NOT include any logos" in get_logo_instruction(2)

    def test_build_designer_prompt_includes_previous_slide_context(self):
        """Designer prompts should reflect prior slide context and language."""
        prompt = build_designer_prompt(
            "Speaker notes",
            "Logo instruction",
            language="zh-CN",
            previous_image_present=True,
        )

        assert "Style Reference (Previous Slide) provided." in prompt
        assert "Simplified Chinese" in prompt
        assert "Speaker notes" in prompt

    def test_build_fallback_prompt_includes_language_constraints(self):
        """Fallback prompts should enforce the target language when needed."""
        prompt = build_fallback_prompt("Notes", language="ja")

        assert "Japanese" in prompt
        assert "NO English text allowed" in prompt

    def test_compute_image_placement_inches_cover_and_contain(self):
        """Placement math should return sane coordinates for both modes."""
        cover = compute_image_placement_inches(1920, 1080, 10.0, 5.625, mode="cover")
        contain = compute_image_placement_inches(1080, 1920, 10.0, 5.625, mode="contain")

        assert cover[2] >= 10.0
        assert cover[3] >= 5.625
        assert contain[0] >= 0
        assert contain[1] >= 0
        assert contain[2] <= 10.0
        assert contain[3] <= 5.625

    def test_optimize_image_file_returns_original_on_failure(self, tmp_path):
        """Image optimization should fall back to the original path on errors."""
        path = tmp_path / "slide.png"
        path.write_bytes(b"raw")

        with patch("services.visual_generator_helpers.Image.open", side_effect=RuntimeError("boom")):
            assert optimize_image_file(str(path)) == str(path)

    def test_optimize_image_file_resaves_png_or_jpeg(self, tmp_path):
        """Optimizing should emit a reduced file when the image opens cleanly."""
        path = tmp_path / "slide.png"
        path.write_bytes(b"raw")

        class FakeImage:
            mode = "RGB"
            format = "PNG"
            info = {}
            size = (100, 100)

            def convert(self, *_args, **_kwargs):
                return self

            def save(self, out_path, format=None, optimize=None, quality=None):
                Path(out_path).write_bytes(b"optimized")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("services.visual_generator_helpers.Image.open", return_value=FakeImage()):
            reduced = optimize_image_file(str(path))

        assert reduced.endswith("_reduced.jpg")
        assert Path(reduced).read_bytes() == b"optimized"

    def test_optimize_image_file_preserves_png_when_transparent(self, tmp_path):
        """Transparent PNGs should stay PNGs after optimization."""
        path = tmp_path / "slide.png"
        path.write_bytes(b"raw")

        class FakeImage:
            mode = "RGBA"
            format = "PNG"
            info = {"transparency": True}

            def save(self, out_path, format=None, optimize=None, quality=None):
                Path(out_path).write_bytes(b"optimized-png")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("services.visual_generator_helpers.Image.open", return_value=FakeImage()):
            reduced = optimize_image_file(str(path))

        assert reduced.endswith("_reduced.png")
        assert Path(reduced).read_bytes() == b"optimized-png"

    def test_apply_slide_notes_writes_plain_text(self):
        """Notes should be written without bullet formatting."""
        paragraph = SimpleNamespace(text="", level=None, alignment=None)
        text_frame = SimpleNamespace(paragraphs=[paragraph], clear=lambda: None)
        slide = SimpleNamespace(has_notes_slide=False, notes_slide=SimpleNamespace(notes_text_frame=text_frame))

        apply_slide_notes(slide, "New notes")

        assert paragraph.text == "New notes"
        assert paragraph.level == 0

    def test_cleanup_reduced_image_file_removes_only_generated_files(self, tmp_path):
        """Cleanup should delete reduced files but keep original files intact."""
        original = tmp_path / "slide.png"
        reduced = tmp_path / "slide_reduced.jpg"
        original.write_bytes(b"original")
        reduced.write_bytes(b"reduced")

        cleanup_reduced_image_file(str(original), str(reduced))

        assert original.exists()
        assert not reduced.exists()

    def test_cleanup_reduced_image_file_ignores_same_path(self, tmp_path):
        """Cleanup should do nothing when the path is unchanged."""
        original = tmp_path / "slide.png"
        original.write_bytes(b"original")

        cleanup_reduced_image_file(str(original), str(original))

        assert original.exists()
