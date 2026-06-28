"""Tests for image utility helpers."""

from unittest.mock import Mock, patch

from PIL import Image

from utils.image_utils import (
    MAX_IMAGE_DIMENSION,
    clear_registry,
    create_image_part,
    get_image,
    register_image,
    resize_image_if_needed,
    unregister_image,
)


class TestImageUtils:
    """Tests for image resizing and registry helpers."""

    def test_resize_image_if_needed_preserves_small_images(self):
        """Images already within limits should be returned unchanged."""
        image = Image.new("RGB", (800, 600), color="white")

        assert resize_image_if_needed(image) is image

    def test_resize_image_if_needed_downscales_large_images(self):
        """Oversized images should be resized to fit the configured max dimension."""
        image = Image.new("RGB", (MAX_IMAGE_DIMENSION + 500, 1000), color="white")

        resized = resize_image_if_needed(image)

        assert max(resized.size) == MAX_IMAGE_DIMENSION

    def test_create_image_part_uses_png_when_small(self):
        """Small images should be serialized as PNG parts."""
        image = Image.new("RGB", (100, 100), color="white")

        with patch("utils.image_utils.types.Part.from_bytes", return_value="part") as mock_from_bytes:
            result = create_image_part(image)

        assert result == "part"
        assert mock_from_bytes.call_args.kwargs["mime_type"] == "image/png"

    def test_create_image_part_converts_transparent_large_images_to_jpeg(self):
        """Large transparent images should be flattened and serialized as JPEG."""
        image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))

        def fake_save(self, buf, format=None, **kwargs):
            if format == "PNG":
                buf.write(b"x" * (5 * 1024 * 1024))
            else:
                buf.write(b"\xff\xd8jpeg")

        with patch("PIL.Image.Image.save", new=fake_save), patch(
            "utils.image_utils.types.Part.from_bytes",
            return_value="part",
        ) as mock_from_bytes:
            result = create_image_part(image)

        assert result == "part"
        assert mock_from_bytes.call_args.kwargs["mime_type"] == "image/jpeg"

    def test_create_image_part_falls_back_to_direct_part_constructor(self):
        """SDKs without from_bytes should use the direct Part constructor path."""
        image = Image.new("RGB", (100, 100), color="white")

        class DummyPart:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        with patch("utils.image_utils.types.Part", new=DummyPart):
            result = create_image_part(image)

        assert result.kwargs["mime_type"] == "image/png"

    def test_image_registry_round_trip(self):
        """Registered images should be retrievable and removable."""
        clear_registry()
        image = Image.new("RGB", (100, 100), color="white")

        register_image("slide_1", image)
        assert get_image("slide_1") is image

        unregister_image("slide_1")
        assert get_image("slide_1") is None
