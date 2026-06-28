"""Tests for presentation processor context helpers."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from services.presentation_processor_context_helpers import get_global_context


class _FakePixmap:
    width = 10
    height = 10
    samples = b"\x00" * 300


class _FakePage:
    def get_pixmap(self, dpi=75):
        return _FakePixmap()


class TestPresentationProcessorContextHelpers:
    """Tests for global context handling branches."""

    def test_returns_cached_context_when_present(self):
        progress = {"global_context": "cached context that is definitely long enough to satisfy the length threshold"}
        progress_file = "/tmp/progress.json"

        result = AsyncMock()

        value = get_global_context(
            pdf_doc=[_FakePage()],
            limit=1,
            progress=progress,
            language="en",
            retry_errors=False,
            progress_file=progress_file,
            output_dir="/tmp/out",
            pptx_path="/tmp/demo.pptx",
            load_progress=Mock(),
            save_progress=Mock(),
            get_progress_file_path=Mock(),
            run_stateless_agent=result,
            overviewer_agent=object(),
            translator_agent=object(),
            build_generation_prompt=lambda count: f"gen {count}",
            build_translation_prompt=lambda a, b, c: "translate",
            language_name_lookup=lambda code: code,
        )

        import asyncio

        assert asyncio.run(value) == progress["global_context"]
        result.assert_not_awaited()

    def test_translates_cached_english_context(self, monkeypatch):
        progress = {}
        load_progress = Mock(return_value={"global_context": "english context that is definitely long enough"})
        save_progress = Mock()
        get_progress_file_path = Mock(return_value="/tmp/en-progress.json")
        translator = AsyncMock(return_value="translated context")

        monkeypatch.setattr("services.presentation_processor_context_helpers.os.path.exists", lambda path: True)

        import asyncio

        value = asyncio.run(
            get_global_context(
                pdf_doc=[_FakePage()],
                limit=1,
                progress=progress,
                language="zh-CN",
                retry_errors=False,
                progress_file="/tmp/progress.json",
                output_dir="/tmp/out",
                pptx_path="/tmp/demo.pptx",
                load_progress=load_progress,
                save_progress=save_progress,
                get_progress_file_path=get_progress_file_path,
                run_stateless_agent=translator,
                overviewer_agent=object(),
                translator_agent=object(),
                build_generation_prompt=lambda count: f"gen {count}",
                build_translation_prompt=lambda a, b, c: f"translate {b}",
                language_name_lookup=lambda code: "Simplified Chinese (简体中文)",
            )
        )

        assert value == "translated context"
        translator.assert_awaited_once()
        save_progress.assert_called_once()

    def test_generates_new_context_when_no_cache(self, monkeypatch):
        progress = {}
        load_progress = Mock()
        save_progress = Mock()
        get_progress_file_path = Mock()
        generator = AsyncMock(return_value="new context")

        monkeypatch.setattr("services.presentation_processor_context_helpers.os.path.exists", lambda path: False)

        import asyncio

        value = asyncio.run(
            get_global_context(
                pdf_doc=[_FakePage()],
                limit=1,
                progress=progress,
                language="en",
                retry_errors=False,
                progress_file="/tmp/progress.json",
                output_dir="/tmp/out",
                pptx_path="/tmp/demo.pptx",
                load_progress=load_progress,
                save_progress=save_progress,
                get_progress_file_path=get_progress_file_path,
                run_stateless_agent=generator,
                overviewer_agent=object(),
                translator_agent=None,
                build_generation_prompt=lambda count: f"gen {count}",
                build_translation_prompt=lambda a, b, c: "translate",
                language_name_lookup=lambda code: code,
            )
        )

        assert value == "new context"
        generator.assert_awaited_once()
        save_progress.assert_called_once()

    def test_retries_generation_when_cached_context_is_present_but_retry_enabled(self, monkeypatch):
        progress = {
            "global_context": "cached context that is definitely long enough to satisfy the length threshold"
        }
        load_progress = Mock()
        save_progress = Mock()
        get_progress_file_path = Mock()
        generator = AsyncMock(return_value="refreshed context")

        monkeypatch.setattr("services.presentation_processor_context_helpers.os.path.exists", lambda path: False)

        import asyncio

        value = asyncio.run(
            get_global_context(
                pdf_doc=[_FakePage()],
                limit=1,
                progress=progress,
                language="en",
                retry_errors=True,
                progress_file="/tmp/progress.json",
                output_dir="/tmp/out",
                pptx_path="/tmp/demo.pptx",
                load_progress=load_progress,
                save_progress=save_progress,
                get_progress_file_path=get_progress_file_path,
                run_stateless_agent=generator,
                overviewer_agent=object(),
                translator_agent=None,
                build_generation_prompt=lambda count: f"gen {count}",
                build_translation_prompt=lambda a, b, c: "translate",
                language_name_lookup=lambda code: code,
            )
        )

        assert value == "refreshed context"
        generator.assert_awaited_once()
        save_progress.assert_called_once()
