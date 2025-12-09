"""Tests for domain entities."""

import pytest
from pathlib import Path
from core.domain import Presentation, Slide, SlideContent, SpeakerNotes


class TestSpeakerNotes:
    """Tests for SpeakerNotes entity."""
    
    def test_creation(self):
        """Test creating speaker notes."""
        notes = SpeakerNotes(text="Hello world", language="en")
        
        assert notes.text == "Hello world"
        assert notes.language == "en"
        assert notes.is_useful is True
        assert notes.needs_regeneration is False
    
    def test_is_empty(self):
        """Test empty notes detection."""
        empty_notes = SpeakerNotes(text="", language="en")
        whitespace_notes = SpeakerNotes(text="   ", language="en")
        valid_notes = SpeakerNotes(text="Content", language="en")
        
        assert empty_notes.is_empty() is True
        assert whitespace_notes.is_empty() is True
        assert valid_notes.is_empty() is False
    
    def test_mark_for_regeneration(self):
        """Test marking notes for regeneration."""
        notes = SpeakerNotes(text="Old content", language="en")
        notes.mark_for_regeneration()
        
        assert notes.needs_regeneration is True
        assert notes.is_useful is False
    
    def test_mark_as_useful(self):
        """Test marking notes as useful."""
        notes = SpeakerNotes(text="Content", language="en")
        notes.mark_for_regeneration()
        notes.mark_as_useful()
        
        assert notes.is_useful is True
        assert notes.needs_regeneration is False
    
    def test_length(self):
        """Test notes length."""
        notes = SpeakerNotes(text="Hello", language="en")
        assert len(notes) == 5
    
    def test_string_representation(self):
        """Test string conversion."""
        notes = SpeakerNotes(text="Test content", language="en")
        assert str(notes) == "Test content"


class TestSlideContent:
    """Tests for SlideContent entity."""
    
    def test_creation(self):
        """Test creating slide content."""
        content = SlideContent(
            topic="Introduction",
            details="Overview of the project",
            visuals="Chart showing growth",
            intent="Introduce the topic"
        )
        
        assert content.topic == "Introduction"
        assert content.details == "Overview of the project"
        assert content.visuals == "Chart showing growth"
        assert content.intent == "Introduce the topic"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        content = SlideContent(
            topic="Test",
            details="Details",
            visuals="Visuals",
            intent="Intent"
        )
        
        result = content.to_dict()
        
        assert result["topic"] == "Test"
        assert result["details"] == "Details"
        assert result["visuals"] == "Visuals"
        assert result["intent"] == "Intent"


class TestSlide:
    """Tests for Slide entity."""
    
    def test_creation(self):
        """Test creating a slide."""
        slide = Slide(index=0, title="Introduction")
        
        assert slide.index == 0
        assert slide.title == "Introduction"
        assert slide.notes is None
        assert slide.has_error is False
    
    def test_invalid_index(self):
        """Test that negative index raises error."""
        with pytest.raises(ValueError, match="Slide index must be non-negative"):
            Slide(index=-1)
    
    def test_has_notes(self):
        """Test notes detection."""
        slide = Slide(index=0)
        assert slide.has_notes() is False
        
        slide.set_notes("Some notes")
        assert slide.has_notes() is True
    
    def test_has_useful_notes(self):
        """Test useful notes detection."""
        slide = Slide(index=0)
        slide.set_notes("Good notes")
        
        assert slide.has_useful_notes() is True
        
        slide.notes.mark_for_regeneration()
        assert slide.has_useful_notes() is False
    
    def test_needs_processing(self):
        """Test processing need detection."""
        slide = Slide(index=0)
        assert slide.needs_processing() is True
        
        slide.set_notes("Notes")
        assert slide.needs_processing() is False
        
        slide.notes.mark_for_regeneration()
        assert slide.needs_processing() is True
    
    def test_mark_error(self):
        """Test error marking."""
        slide = Slide(index=0)
        slide.mark_error("Test error")
        
        assert slide.has_error is True
        assert slide.error_message == "Test error"
    
    def test_clear_error(self):
        """Test error clearing."""
        slide = Slide(index=0)
        slide.mark_error("Error")
        slide.clear_error()
        
        assert slide.has_error is False
        assert slide.error_message is None
    
    def test_set_content(self):
        """Test setting slide content."""
        slide = Slide(index=0)
        slide.set_content(
            topic="Test",
            details="Details",
            visuals="Visuals",
            intent="Intent"
        )
        
        assert slide.content is not None
        assert slide.content.topic == "Test"


class TestPresentation:
    """Tests for Presentation entity."""
    
    @pytest.fixture
    def temp_files(self, tmp_path):
        """Create temporary test files."""
        pptx_file = tmp_path / "test.pptx"
        pdf_file = tmp_path / "test.pdf"
        pptx_file.touch()
        pdf_file.touch()
        return pptx_file, pdf_file
    
    def test_creation(self, temp_files):
        """Test creating a presentation."""
        pptx_path, pdf_path = temp_files
        
        pres = Presentation(
            pptx_path=pptx_path,
            pdf_path=pdf_path,
            language="en"
        )
        
        assert pres.pptx_path == pptx_path
        assert pres.pdf_path == pdf_path
        assert pres.language == "en"
        assert len(pres.slides) == 0
    
    def test_missing_files(self, tmp_path):
        """Test that missing files raise error."""
        with pytest.raises(ValueError, match="PPTX file not found"):
            Presentation(
                pptx_path=tmp_path / "missing.pptx",
                pdf_path=tmp_path / "test.pdf"
            )
    
    def test_add_slide(self, temp_files):
        """Test adding slides."""
        pptx_path, pdf_path = temp_files
        pres = Presentation(pptx_path=pptx_path, pdf_path=pdf_path)
        
        slide = Slide(index=0, title="Test")
        pres.add_slide(slide)
        
        assert pres.total_slides() == 1
        assert pres.get_slide(0) == slide
    
    def test_get_slide(self, temp_files):
        """Test getting slide by index."""
        pptx_path, pdf_path = temp_files
        pres = Presentation(pptx_path=pptx_path, pdf_path=pdf_path)
        
        slide1 = Slide(index=0)
        slide2 = Slide(index=1)
        pres.add_slide(slide1)
        pres.add_slide(slide2)
        
        assert pres.get_slide(0) == slide1
        assert pres.get_slide(1) == slide2
        assert pres.get_slide(2) is None
    
    def test_progress_tracking(self, temp_files):
        """Test progress tracking."""
        pptx_path, pdf_path = temp_files
        pres = Presentation(pptx_path=pptx_path, pdf_path=pdf_path)
        
        slide1 = Slide(index=0)
        slide2 = Slide(index=1)
        slide1.set_notes("Notes 1")
        pres.add_slide(slide1)
        pres.add_slide(slide2)
        
        assert pres.total_slides() == 2
        assert pres.processed_slides() == 1
        assert pres.progress_percentage() == 50.0
        assert pres.is_complete() is False
    
    def test_is_complete(self, temp_files):
        """Test completion detection."""
        pptx_path, pdf_path = temp_files
        pres = Presentation(pptx_path=pptx_path, pdf_path=pdf_path)
        
        slide1 = Slide(index=0)
        slide2 = Slide(index=1)
        slide1.set_notes("Notes 1")
        slide2.set_notes("Notes 2")
        pres.add_slide(slide1)
        pres.add_slide(slide2)
        
        assert pres.is_complete() is True
    
    def test_get_output_path(self, temp_files):
        """Test output path generation."""
        pptx_path, pdf_path = temp_files
        
        # English presentation, no style
        pres_en = Presentation(pptx_path=pptx_path, pdf_path=pdf_path, language="en")
        output_en = pres_en.get_output_path()
        assert output_en.name == "test_notes.pptx"
        
        # Chinese presentation
        pres_zh = Presentation(pptx_path=pptx_path, pdf_path=pdf_path, language="zh-CN")
        output_zh = pres_zh.get_output_path()
        assert output_zh.name == "test_zh-CN_notes.pptx"
        
        # With style (style NOT in filename, only in folder structure)
        pres_style = Presentation(pptx_path=pptx_path, pdf_path=pdf_path, language="en", style="Cyberpunk")
        output_style = pres_style.get_output_path()
        assert output_style.name == "test_notes.pptx"  # No style in filename
        
        # With style and language (only language in filename)
        pres_both = Presentation(pptx_path=pptx_path, pdf_path=pdf_path, language="zh-CN", style="Gundam")
        output_both = pres_both.get_output_path()
        assert output_both.name == "test_zh-CN_notes.pptx"  # Only language, no style
        
        # With output directory
        output_dir = temp_files[0].parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_custom = pres_style.get_output_path(output_dir=output_dir)
        assert output_custom.parent == output_dir
        assert output_custom.name == "test_notes.pptx"  # No style in filename
