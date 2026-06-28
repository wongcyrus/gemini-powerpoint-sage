"""Tests for NotesGenerator."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from PIL import Image

from services.notes_generator import NotesGenerator
from utils.error_handling import SlideProcessingError


class TestNotesGenerator:
    """Tests for NotesGenerator class."""
    
    def test_initialization(self, mock_tool_factory, mock_supervisor_runner):
        """Test generator initialization."""
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="en",
            english_notes={}
        )
        
        assert generator.tool_factory == mock_tool_factory
        assert generator.supervisor_runner == mock_supervisor_runner
        assert generator.language == "en"
        assert generator.english_notes == {}
    
    def test_should_translate_true(
        self,
        mock_tool_factory,
        mock_supervisor_runner,
        sample_english_notes
    ):
        """Test should_translate returns True for non-English with notes."""
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="zh-CN",
            english_notes=sample_english_notes
        )
        
        assert generator._should_translate(1) is True
        assert generator._should_translate(2) is True
    
    def test_should_translate_false_english(
        self,
        mock_tool_factory,
        mock_supervisor_runner
    ):
        """Test should_translate returns False for English."""
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="en",
            english_notes={1: "Note"}
        )
        
        assert generator._should_translate(1) is False
    
    def test_should_translate_false_no_notes(
        self,
        mock_tool_factory,
        mock_supervisor_runner
    ):
        """Test should_translate returns False when no English notes."""
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="zh-CN",
            english_notes={}
        )
        
        assert generator._should_translate(1) is False
    
    @pytest.mark.asyncio
    async def test_translate_notes_success(
        self,
        mock_tool_factory,
        mock_supervisor_runner,
        sample_english_notes
    ):
        """Test successful notes translation."""
        async def mock_translator(text, **kwargs):
            return f"Translated: {text}"
        
        mock_tool_factory.create_translator_tool.return_value = mock_translator
        
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="zh-CN",
            english_notes=sample_english_notes
        )
        
        notes, status = await generator._translate_notes(1)
        
        assert "Translated:" in notes
        assert status == "success"
    
    @pytest.mark.asyncio
    async def test_translate_notes_empty_result(
        self,
        mock_tool_factory,
        mock_supervisor_runner,
        sample_english_notes
    ):
        """Test translation with empty result."""
        async def mock_translator(text, **kwargs):
            return ""
        
        mock_tool_factory.create_translator_tool.return_value = mock_translator
        
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="zh-CN",
            english_notes=sample_english_notes
        )
        
        notes, status = await generator._translate_notes(1)
        
        assert notes == ""
        assert status == "error"
    
    @pytest.mark.asyncio
    async def test_generate_notes_translation_mode(
        self,
        mock_tool_factory,
        mock_supervisor_runner,
        sample_english_notes,
        sample_image
    ):
        """Test generate_notes in translation mode."""
        async def mock_translator(text, **kwargs):
            return "翻译的笔记"
        
        mock_tool_factory.create_translator_tool.return_value = mock_translator
        
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="zh-CN",
            english_notes=sample_english_notes
        )
        
        notes, status = await generator.generate_notes(
            slide_idx=1,
            slide_image=sample_image,
            existing_notes="",
            previous_slide_summary="",
            presentation_theme="Test",
            global_context="Context"
        )
        
        assert notes == "翻译的笔记"
        assert status == "success"
    
    def test_build_supervisor_prompt(
        self,
        mock_tool_factory,
        mock_supervisor_runner
    ):
        """Test building supervisor prompt."""
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="en"
        )
        
        prompt = generator._build_supervisor_prompt(
            slide_idx=1,
            image_id="slide_1",
            existing_notes="Old notes",
            previous_slide_summary="Previous",
            presentation_theme="Security",
            global_context="Global"
        )
        
        assert "Slide 1" in prompt
        assert "slide_1" in prompt
        assert "Old notes" in prompt
        assert "Previous" in prompt
        assert "Security" in prompt
        assert "Global" in prompt

    @pytest.mark.asyncio
    async def test_generate_notes_supervisor_mode(
        self,
        mock_tool_factory,
        mock_supervisor_runner,
        sample_image
    ):
        """Test generate_notes delegates to supervisor mode for English flows."""
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="en",
        )

        with patch.object(
            generator,
            "_generate_with_supervisor",
            AsyncMock(return_value=("Generated notes", "success")),
        ) as mock_generate:
            notes, status = await generator.generate_notes(
                slide_idx=2,
                slide_image=sample_image,
                existing_notes="seed",
                previous_slide_summary="prev",
                presentation_theme="Theme",
                global_context="Context",
            )

        assert (notes, status) == ("Generated notes", "success")
        mock_generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_translate_notes_exception_returns_error(
        self,
        mock_tool_factory,
        mock_supervisor_runner,
        sample_english_notes
    ):
        """Test translation exceptions are converted into error status."""
        async def mock_translator(text, **kwargs):
            raise RuntimeError("translator failed")

        mock_tool_factory.create_translator_tool.return_value = mock_translator
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="zh-CN",
            english_notes=sample_english_notes,
        )

        notes, status = await generator._translate_notes(1)

        assert notes == ""
        assert status == "error"

    @pytest.mark.asyncio
    async def test_run_supervisor_collects_text_and_resets_writer_output(
        self,
        mock_tool_factory,
        sample_image
    ):
        """Test supervisor execution returns collected text from streamed events."""
        async def run_async(**kwargs):
            part = Mock(text="Generated answer", function_call=None)
            event = Mock()
            event.content = Mock(parts=[part])
            yield event

        mock_runner = Mock()
        mock_runner.run_async = run_async
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_runner,
            language="en",
        )

        notes, status = await generator._run_supervisor(
            slide_idx=1,
            content=Mock(),
            user_id="u",
            session_id="s",
        )

        assert (notes, status) == ("Generated answer", "success")
        mock_tool_factory.reset_writer_output.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_supervisor_uses_last_writer_output_fallback(
        self,
        mock_tool_factory
    ):
        """Test empty supervisor output falls back to the writer tool result."""
        async def run_async(**kwargs):
            if False:
                yield None

        mock_tool_factory.last_writer_output = "Fallback output"
        mock_runner = Mock()
        mock_runner.run_async = run_async
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_runner,
            language="en",
        )

        notes, status = await generator._run_supervisor(
            slide_idx=3,
            content=Mock(),
            user_id="u",
            session_id="s",
        )

        assert (notes, status) == ("Fallback output", "success")
        mock_tool_factory.reset_writer_output.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_supervisor_raises_on_tool_error_response(
        self,
        mock_tool_factory
    ):
        """Structured tool errors in supervisor output should raise slide errors."""
        async def run_async(**kwargs):
            part = Mock(text="tool_error: failed to write", function_call=None)
            event = Mock()
            event.content = Mock(parts=[part])
            yield event

        mock_runner = Mock()
        mock_runner.run_async = run_async
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_runner,
            language="en",
        )

        with pytest.raises(SlideProcessingError, match="Tool error"):
            await generator._run_supervisor(
                slide_idx=4,
                content=Mock(),
                user_id="u",
                session_id="s",
            )

    @pytest.mark.asyncio
    async def test_run_supervisor_raises_when_no_output_is_available(
        self,
        mock_tool_factory
    ):
        """Missing supervisor and fallback output should raise a retryable error."""
        async def run_async(**kwargs):
            if False:
                yield None

        mock_runner = Mock()
        mock_runner.run_async = run_async
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_runner,
            language="en",
        )

        with pytest.raises(SlideProcessingError, match="empty response"):
            await generator._run_supervisor(
                slide_idx=5,
                content=Mock(),
                user_id="u",
                session_id="s",
            )

    def test_is_error_response_matches_only_structured_errors(
        self,
        mock_tool_factory,
        mock_supervisor_runner
    ):
        """Error detection should be strict to avoid false positives in real notes."""
        generator = NotesGenerator(
            tool_factory=mock_tool_factory,
            supervisor_runner=mock_supervisor_runner,
            language="en",
        )

        assert generator._is_error_response("tool_error: failed") is True
        assert generator._is_error_response("system_error: failed") is True
        assert generator._is_error_response("normal speaker notes about system error handling") is False
