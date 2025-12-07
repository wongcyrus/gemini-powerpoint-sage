"""Tests for ContextService."""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from PIL import Image

from services.context_service import ContextService


class TestContextService:
    """Tests for ContextService class."""
    
    def test_initialization(self, mock_agent):
        """Test service initialization."""
        service = ContextService(
            overviewer_agent=mock_agent,
            translator_agent=mock_agent
        )
        
        assert service.overviewer_agent == mock_agent
        assert service.translator_agent == mock_agent
    
    @pytest.mark.asyncio
    async def test_get_global_context_cached(self, mock_agent, sample_progress_data):
        """Test getting cached global context."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(sample_progress_data, f)
            progress_file = f.name
        
        try:
            service = ContextService(overviewer_agent=mock_agent)
            
            context = await service.get_global_context(
                pdf_doc=Mock(),
                limit=3,
                progress_file=progress_file,
                language="en",
                retry_errors=False
            )
            
            assert context == sample_progress_data["global_context"]
        finally:
            os.unlink(progress_file)
    
    @pytest.mark.asyncio
    async def test_get_global_context_generate_new(self, mock_agent):
        """Test generating new global context."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump({"slides": {}}, f)
            progress_file = f.name
        
        try:
            # Mock PDF document
            mock_pdf = Mock()
            mock_page = Mock()
            mock_pix = Mock()
            mock_pix.width = 800
            mock_pix.height = 600
            mock_pix.samples = b'\x00' * (800 * 600 * 3)
            mock_page.get_pixmap.return_value = mock_pix
            mock_pdf.__getitem__ = Mock(return_value=mock_page)
            
            with patch('services.context_service.run_stateless_agent') as mock_run:
                mock_run.return_value = "Generated global context"
                
                service = ContextService(overviewer_agent=mock_agent)
                
                context = await service.get_global_context(
                    pdf_doc=mock_pdf,
                    limit=1,
                    progress_file=progress_file,
                    language="en"
                )
                
                assert context == "Generated global context"
                mock_run.assert_called_once()
        finally:
            os.unlink(progress_file)
    
    def test_load_english_notes_success(self, sample_english_notes):
        """Test loading English notes successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock English progress file
            progress_data = {
                "slides": {
                    "slide_1_abc": {
                        "slide_index": 1,
                        "note": "English note 1",
                        "status": "success"
                    },
                    "slide_2_def": {
                        "slide_index": 2,
                        "note": "English note 2",
                        "status": "success"
                    }
                }
            }
            
            import json
            en_progress_file = os.path.join(tmpdir, "test_en_progress.json")
            with open(en_progress_file, 'w') as f:
                json.dump(progress_data, f)
            
            with patch('services.context_service.get_progress_file_path') as mock_path:
                mock_path.return_value = en_progress_file
                
                service = ContextService(overviewer_agent=Mock())
                
                notes = service.load_english_notes(
                    pptx_path=os.path.join(tmpdir, "test.pptx"),
                    language="zh-CN"
                )
                
                assert len(notes) == 2
                assert notes[1] == "English note 1"
                assert notes[2] == "English note 2"
    
    def test_load_english_notes_for_english(self):
        """Test loading English notes when language is English returns empty."""
        service = ContextService(overviewer_agent=Mock())
        
        notes = service.load_english_notes(
            pptx_path="/path/to/test.pptx",
            language="en"
        )
        
        assert notes == {}
    
    def test_load_english_notes_file_not_found(self):
        """Test loading English notes when file doesn't exist."""
        with patch('services.context_service.get_progress_file_path') as mock_path:
            mock_path.return_value = "/nonexistent/file.json"
            
            service = ContextService(overviewer_agent=Mock())
            
            notes = service.load_english_notes(
                pptx_path="/path/to/test.pptx",
                language="zh-CN"
            )
            
            assert notes == {}
    
    def test_has_cached_context_true(self):
        """Test checking for cached context returns True."""
        service = ContextService(overviewer_agent=Mock())
        
        progress = {
            "global_context": "This is a valid context with more than 50 characters for testing."
        }
        
        result = service._has_cached_context(progress, retry_errors=False)
        assert result is True
    
    def test_has_cached_context_false_short(self):
        """Test checking for cached context returns False for short context."""
        service = ContextService(overviewer_agent=Mock())
        
        progress = {
            "global_context": "Short"
        }
        
        result = service._has_cached_context(progress, retry_errors=False)
        assert result is False
    
    def test_has_cached_context_false_retry(self):
        """Test checking for cached context returns False when retry_errors is True."""
        service = ContextService(overviewer_agent=Mock())
        
        progress = {
            "global_context": "This is a valid context with more than 50 characters."
        }
        
        result = service._has_cached_context(progress, retry_errors=True)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_translate_from_english_success(self, mock_agent):
        """Test translating global context from English."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create English progress file
            en_progress = {
                "global_context": "English global context for the presentation."
            }
            
            import json
            en_progress_file = os.path.join(tmpdir, "test_en_progress.json")
            with open(en_progress_file, 'w') as f:
                json.dump(en_progress, f)
            
            with patch('services.context_service.get_progress_file_path') as mock_path:
                mock_path.return_value = en_progress_file
                
                with patch('services.context_service.run_stateless_agent') as mock_run:
                    mock_run.return_value = "翻译的全局上下文"
                    
                    service = ContextService(
                        overviewer_agent=Mock(),
                        translator_agent=mock_agent
                    )
                    
                    result = await service._translate_from_english(
                        pptx_path=os.path.join(tmpdir, "test.pptx"),
                        target_language="zh-CN"
                    )
                    
                    assert result == "翻译的全局上下文"
    
    @pytest.mark.asyncio
    async def test_translate_from_english_no_agent(self):
        """Test translating without translator agent returns None."""
        service = ContextService(
            overviewer_agent=Mock(),
            translator_agent=None
        )
        
        result = await service._translate_from_english(
            pptx_path="/path/to/test.pptx",
            target_language="zh-CN"
        )
        
        assert result is None
    
    def test_extract_all_images(self, mock_agent):
        """Test extracting all images from PDF."""
        # Mock PDF document
        mock_pdf = Mock()
        mock_page = Mock()
        mock_pix = Mock()
        mock_pix.width = 800
        mock_pix.height = 600
        mock_pix.samples = b'\x00' * (800 * 600 * 3)
        mock_page.get_pixmap.return_value = mock_pix
        mock_pdf.__getitem__ = Mock(return_value=mock_page)
        
        service = ContextService(overviewer_agent=mock_agent)
        
        images = service._extract_all_images(mock_pdf, limit=2)
        
        assert len(images) == 2
        assert all(isinstance(img, Image.Image) for img in images)
