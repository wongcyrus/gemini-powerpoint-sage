"""Tests for visual generator wrapper methods."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from services.visual_generator import VisualGenerator


class TestVisualGeneratorWrappers:
    """Tests for delegation on VisualGenerator methods."""

    def _make_generator(self):
        generator = VisualGenerator.__new__(VisualGenerator)
        generator.previous_image = None
        return generator

    def test_logo_instruction_delegates_to_helper(self):
        """Logo instructions should stay tied to slide position."""
        generator = self._make_generator()
        assert "logo/branding" in generator._get_logo_instruction(1)
        assert "DO NOT include any logos" in generator._get_logo_instruction(2)

    def test_prompt_builders_delegate_to_helpers(self):
        """Prompt builders should remain thin wrappers."""
        generator = self._make_generator()
        generator.previous_image = object()

        designer = generator._build_designer_prompt("notes", "logo", "zh-CN")
        fallback = generator._build_fallback_prompt("notes", "ja")

        assert "Simplified Chinese" in designer
        assert "Style Reference" in designer
        assert "Japanese" in fallback

    def test_compute_image_placement_wrapper_returns_length_like_values(self):
        """Placement wrapper should still return PowerPoint length objects."""
        generator = self._make_generator()
        slide_size = SimpleNamespace(inches=10.0)
        left, top, width, height = generator._compute_image_placement(
            1920,
            1080,
            slide_size,
            SimpleNamespace(inches=5.625),
            mode="cover",
        )

        assert hasattr(left, "inches")
        assert hasattr(top, "inches")
        assert hasattr(width, "inches")
        assert hasattr(height, "inches")

    @pytest.mark.asyncio
    async def test_generate_visual_skip_and_existing_file(self, tmp_path):
        """Visual generation should skip or reuse existing files when available."""
        generator = VisualGenerator(Mock(), str(tmp_path), skip_generation=True)
        image = Image.new("RGB", (100, 100), color="white")
        assert await generator.generate_visual(1, image, "notes") is None

        generator = VisualGenerator(Mock(), str(tmp_path))
        existing = tmp_path / "slide_2_reimagined.png"
        image.save(existing)

        with patch("services.visual_generator.rotate_project", return_value="proj"):
            result = await generator.generate_visual(2, image, "notes")

        assert result is not None
        assert generator.previous_image is not None

    @pytest.mark.asyncio
    async def test_generate_visual_primary_and_fallback_paths(self, tmp_path):
        """Primary generation should save output and fallback should still work."""
        generator = VisualGenerator(Mock(instruction="prompt"), str(tmp_path))
        image = Image.new("RGB", (100, 100), color="white")

        with patch("services.visual_generator.rotate_project", return_value="proj"), patch(
            "services.visual_generator.run_visual_agent", return_value=b"image-bytes"
        ), patch("services.visual_generator.os.getenv", return_value=None):
            result = await generator.generate_visual(3, image, "notes")

        saved = tmp_path / "slide_3_reimagined.png"
        assert result == b"image-bytes"
        assert saved.exists()

        generator = VisualGenerator(Mock(instruction="prompt"), str(tmp_path))
        with patch("services.visual_generator.rotate_project", return_value="proj"), patch(
            "services.visual_generator.os.getenv", return_value="1"
        ), patch.object(generator, "_generate_imagen_directly", return_value=b"fallback-bytes"):
            result = await generator.generate_visual(4, image, "notes")

        assert result == b"fallback-bytes"

    @pytest.mark.asyncio
    async def test_generate_visual_candidate_uses_secondary_model(self, tmp_path):
        """The helper should fall through to the secondary model when primary fails."""
        generator = VisualGenerator(Mock(instruction="prompt"), str(tmp_path))
        image = Image.new("RGB", (100, 100), color="white")

        with patch("services.visual_generator.rotate_project", return_value="proj"), patch(
            "services.visual_generator.os.getenv", return_value=None
        ), patch("services.visual_generator.run_visual_agent", side_effect=[None, b"secondary-bytes"]) as run_agent, patch(
            "google.adk.agents.LlmAgent"
        ) as secondary_cls:
            result = await generator._generate_visual_candidate(5, image, "notes", "en")

        assert result == b"secondary-bytes"
        assert run_agent.call_count == 2
        secondary_cls.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_visual_force_fallback_skips_primary(self, tmp_path):
        """Force fallback should bypass the primary and secondary model tiers."""
        generator = VisualGenerator(Mock(instruction="prompt"), str(tmp_path))
        image = Image.new("RGB", (100, 100), color="white")

        with patch("services.visual_generator.rotate_project", return_value="proj"), patch(
            "services.visual_generator.os.getenv", return_value="1"
        ), patch("services.visual_generator.run_visual_agent") as run_agent, patch.object(
            generator, "_generate_imagen_directly", return_value=b"imagen-bytes"
        ):
            result = await generator.generate_visual(6, image, "notes")

        assert result == b"imagen-bytes"
        run_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_visual_candidate_falls_back_after_secondary_exception(self, tmp_path):
        """Secondary model exceptions should still fall through to Imagen."""
        generator = VisualGenerator(Mock(instruction="prompt"), str(tmp_path))
        image = Image.new("RGB", (100, 100), color="white")

        with patch("services.visual_generator.rotate_project", return_value="proj"), patch(
            "services.visual_generator.os.getenv", return_value=None
        ), patch("services.visual_generator.run_visual_agent", side_effect=[None, Exception("secondary failed")]), patch.object(
            generator, "_generate_imagen_directly", return_value=b"imagen-bytes"
        ):
            result = await generator._generate_visual_candidate(7, image, "notes", "en")

        assert result == b"imagen-bytes"

    @pytest.mark.asyncio
    async def test_generate_visual_no_image_resets_style_context(self, tmp_path):
        """If every tier fails, the generator should clear the cached style context."""
        generator = VisualGenerator(Mock(instruction="prompt"), str(tmp_path))
        image = Image.new("RGB", (100, 100), color="white")
        generator.previous_image = Image.new("RGB", (32, 32), color="black")

        with patch("services.visual_generator.rotate_project", return_value="proj"), patch(
            "services.visual_generator.os.getenv", return_value="1"
        ), patch.object(generator, "_generate_imagen_directly", return_value=None):
            result = await generator.generate_visual(8, image, "notes")

        assert result is None
        assert generator.previous_image is None

    def test_load_existing_visual_bytes_returns_none_when_read_fails(self, tmp_path):
        """Existing-file reuse should fall back to regeneration when read fails."""
        generator = self._make_generator()
        img_path = tmp_path / "slide_1_reimagined.png"
        img_path.write_bytes(b"img")

        with patch("services.visual_generator.os.path.exists", return_value=True), patch(
            "builtins.open", side_effect=OSError("boom")
        ):
            assert generator._load_existing_visual_bytes(str(img_path), 1, img_path.name, retry_errors=False) is None

    @pytest.mark.asyncio
    async def test_generate_visual_save_failure_keeps_generated_bytes(self, tmp_path):
        """Save failures should not discard the generated image bytes."""
        generator = VisualGenerator(Mock(instruction="prompt"), str(tmp_path))
        image = Image.new("RGB", (100, 100), color="white")

        with patch("services.visual_generator.rotate_project", return_value="proj"), patch(
            "services.visual_generator.run_visual_agent", return_value=b"image-bytes"
        ), patch("services.visual_generator.os.getenv", return_value=None), patch(
            "builtins.open", side_effect=OSError("save failed")
        ):
            result = await generator.generate_visual(9, image, "notes")

        assert result == b"image-bytes"
        assert generator.previous_image is None

    def test_update_previous_image_invalid_bytes_clears_context(self):
        """Invalid image bytes should reset the style context."""
        generator = self._make_generator()

        with patch("services.visual_generator.Image.open", side_effect=OSError("bad image")):
            generator._update_previous_image(b"bad")

        assert generator.previous_image is None

    @pytest.mark.asyncio
    async def test_generate_imagen_directly_returns_bytes(self, monkeypatch):
        """Imagen fallback should surface returned image bytes."""
        generator = self._make_generator()
        generator.fallback_imagen_model = "imagen-test"

        class _Image:
            image_bytes = b"imagen"

        class _Response:
            generated_images = [SimpleNamespace(image=_Image())]

        class _Client:
            class models:
                @staticmethod
                def generate_images(model, prompt, config):
                    return _Response()

        monkeypatch.setattr("services.visual_generator.rotate_project", lambda: "proj")
        monkeypatch.setattr("services.visual_generator.genai.Client", lambda: _Client())

        result = await generator._generate_imagen_directly("prompt")

        assert result == b"imagen"

    @pytest.mark.asyncio
    async def test_generate_imagen_directly_handles_empty_response(self, monkeypatch):
        """Imagen fallback should return None when no images are produced."""
        generator = self._make_generator()
        generator.fallback_imagen_model = "imagen-test"

        class _Response:
            generated_images = []

        class _Client:
            class models:
                @staticmethod
                def generate_images(model, prompt, config):
                    return _Response()

        monkeypatch.setattr("services.visual_generator.rotate_project", lambda: "proj")
        monkeypatch.setattr("services.visual_generator.genai.Client", lambda: _Client())

        result = await generator._generate_imagen_directly("prompt")

        assert result is None

    def test_replace_slide_with_visual_success(self, tmp_path):
        """Replacing a slide should remove shapes, add the image, and attach notes."""
        generator = self._make_generator()
        image_path = tmp_path / "slide.png"
        image_path.write_bytes(b"img")

        class _ShapeElement:
            def getparent(self):
                return self

            def remove(self, _element):
                return None

        class _Shape:
            def __init__(self):
                self.element = _ShapeElement()

        class _Picture:
            width = SimpleNamespace(inches=1)
            height = SimpleNamespace(inches=1)

        added = []

        class _Shapes(list):
            def add_picture(self, *args, **kwargs):
                added.append((args, kwargs))
                return _Picture()

        slide = SimpleNamespace(
            shapes=_Shapes([_Shape()]),
            has_notes_slide=False,
            notes_slide=SimpleNamespace(notes_text_frame=SimpleNamespace(clear=lambda: None, paragraphs=[SimpleNamespace(text="", level=None, alignment=None)])),
        )
        prs = SimpleNamespace(slide_width=SimpleNamespace(inches=10.0), slide_height=SimpleNamespace(inches=5.625))

        class _Image:
            size = (800, 600)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("services.visual_generator.optimize_image_file", return_value=str(image_path)), patch(
            "services.visual_generator.Image.open", return_value=_Image()
        ), patch("services.visual_generator.cleanup_reduced_image_file"), patch(
            "services.visual_generator.apply_slide_notes"
        ) as apply_notes:
            assert generator.replace_slide_with_visual(prs, slide, str(image_path), "notes") is True

        assert added
        apply_notes.assert_called_once()

    def test_add_visual_to_presentation_falls_back_to_first_layout(self, tmp_path):
        """Adding a slide should fall back when the blank layout is missing."""
        generator = self._make_generator()
        image_path = tmp_path / "slide.png"
        image_path.write_bytes(b"img")

        class _Picture:
            width = SimpleNamespace(inches=1)
            height = SimpleNamespace(inches=1)

        class _Shapes(list):
            def add_picture(self, *args, **kwargs):
                return _Picture()

        class _Slide:
            def __init__(self):
                self.shapes = _Shapes()

        class _Slides(list):
            def add_slide(self, layout):
                slide = _Slide()
                self.append(slide)
                return slide

        prs = SimpleNamespace(
            slide_layouts=[object()],
            slides=_Slides(),
            slide_width=SimpleNamespace(inches=10.0),
            slide_height=SimpleNamespace(inches=5.625),
        )

        class _Image:
            size = (800, 600)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("services.visual_generator.optimize_image_file", return_value=str(image_path)), patch(
            "services.visual_generator.Image.open", return_value=_Image()
        ), patch("services.visual_generator.cleanup_reduced_image_file"), patch(
            "services.visual_generator.apply_slide_notes"
        ):
            assert generator.add_visual_to_presentation(prs, 1, str(image_path), "notes") is True
