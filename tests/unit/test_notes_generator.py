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
        async def mock_translator(text):
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
        async def mock_translator(text):
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
        async def mock_translator(text):
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
