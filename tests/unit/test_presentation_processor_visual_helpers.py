"""Tests for presentation processor visual helpers."""

from PIL import Image
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from services.presentation_processor_helpers import (
    build_english_visuals_dir,
    process_slide_visual,
)


class TestPresentationProcessorVisualHelpers:
    """Tests for slide visual branch helpers."""

    def test_build_english_visuals_dir(self):
        assert build_english_visuals_dir("/tmp/out", "/tmp/demo.pptx") == "/tmp/out/demo_en_visuals"
        assert build_english_visuals_dir("/tmp/out/demo_zh-CN_visuals", "/tmp/demo.pptx") == "/tmp/out/demo_en_visuals"

    def test_process_slide_visual_reuses_existing_translated_visual(self, tmp_path):
        visuals_dir = tmp_path / "visuals"
        visuals_dir.mkdir()
        target_img = visuals_dir / "slide_1_reimagined.png"
        target_img.write_bytes(b"img")

        replace_calls = []

        async def _never_called(*args, **kwargs):
            raise AssertionError("run_visual_agent should not be called")

        class _VG:
            async def generate_visual(self, *args, **kwargs):
                raise AssertionError("generate_visual should not be called")

        import asyncio

        result = asyncio.run(
            process_slide_visual(
                slide_idx=1,
                slide_visuals=SimpleNamespace(),
                slide_image=SimpleNamespace(),
                speaker_notes="notes",
                status="success",
                language="zh-CN",
                visuals_dir=str(visuals_dir),
                pptx_path=str(tmp_path / "demo.pptx"),
                retry_errors=False,
                image_translator_agent=object(),
                visual_generator=_VG(),
                replace_visual=lambda *args: replace_calls.append(args),
                run_visual_agent=AsyncMock(side_effect=_never_called),
                get_language_name=lambda code: "Simplified Chinese (简体中文)",
            )
        )

        assert result == 0
        assert replace_calls == [(SimpleNamespace(), str(target_img), "notes")]

    def test_process_slide_visual_reruns_existing_translated_visual_when_retrying(self, tmp_path):
        visuals_dir = tmp_path / "visuals"
        visuals_dir.mkdir()
        target_img = visuals_dir / "slide_1_reimagined.png"
        target_img.write_bytes(b"img")

        replace_calls = []

        vg = SimpleNamespace(generate_visual=AsyncMock(return_value=b"new-bytes"))

        import asyncio

        result = asyncio.run(
            process_slide_visual(
                slide_idx=1,
                slide_visuals=SimpleNamespace(),
                slide_image=SimpleNamespace(),
                speaker_notes="notes",
                status="success",
                language="zh-CN",
                visuals_dir=str(visuals_dir),
                pptx_path=str(tmp_path / "demo.pptx"),
                retry_errors=True,
                image_translator_agent=object(),
                visual_generator=vg,
                replace_visual=lambda *args: replace_calls.append(args),
                run_visual_agent=AsyncMock(),
                get_language_name=lambda code: "Simplified Chinese (简体中文)",
            )
        )

        assert result == 0
        vg.generate_visual.assert_awaited_once()
        assert replace_calls == [(SimpleNamespace(), str(target_img), "notes")]

    def test_process_slide_visual_translates_existing_english_visual(self, tmp_path):
        visuals_dir = tmp_path / "visuals"
        visuals_dir.mkdir()
        english_dir = visuals_dir / "demo_en_visuals"
        english_dir.mkdir()

        en_img = english_dir / "slide_2_reimagined.png"
        Image.new("RGB", (32, 32), color="white").save(en_img)

        replace_calls = []

        class _VG:
            async def generate_visual(self, *args, **kwargs):
                raise AssertionError("generate_visual should not be called")

        import asyncio

        result = asyncio.run(
            process_slide_visual(
                slide_idx=2,
                slide_visuals=SimpleNamespace(),
                slide_image=SimpleNamespace(),
                speaker_notes="translated notes",
                status="success",
                language="zh-CN",
                visuals_dir=str(visuals_dir),
                pptx_path=str(tmp_path / "demo.pptx"),
                retry_errors=False,
                image_translator_agent=object(),
                visual_generator=_VG(),
                replace_visual=lambda *args: replace_calls.append(args),
                run_visual_agent=AsyncMock(return_value=b"translated-bytes"),
                get_language_name=lambda code: "Simplified Chinese (简体中文)",
            )
        )

        assert result == 0
        assert replace_calls == [
            (
                SimpleNamespace(),
                str(visuals_dir / "slide_2_reimagined.png"),
                "translated notes",
            )
        ]
