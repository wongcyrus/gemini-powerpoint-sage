"""Tests for FileService."""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch

from services.file_service import FileService
from utils.error_handling import ProcessingError


class TestFileService:
    """Tests for FileService class."""
    
    def test_load_presentation_success(self):
        """Test loading presentation successfully."""
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
            pptx_path = f.name
        
        try:
            with patch('services.file_service.Presentation') as mock_prs:
                mock_prs.return_value = Mock()
                
                result = FileService.load_presentation(pptx_path)
                
                assert result is not None
                mock_prs.assert_called_once_with(pptx_path)
        finally:
            if os.path.exists(pptx_path):
                os.unlink(pptx_path)
    
    def test_load_presentation_failure(self):
        """Test loading presentation with error."""
        with pytest.raises(ProcessingError, match="Failed to load PPTX"):
            FileService.load_presentation("/nonexistent/file.pptx")
    
    def test_load_pdf_success(self):
        """Test loading PDF successfully."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            with patch('services.file_service.pymupdf.open') as mock_open:
                mock_open.return_value = Mock()
                
                result = FileService.load_pdf(pdf_path)
                
                assert result is not None
                mock_open.assert_called_once_with(pdf_path)
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    def test_load_pdf_failure(self):
        """Test loading PDF with error."""
        with pytest.raises(ProcessingError, match="Failed to load PDF"):
            FileService.load_pdf("/nonexistent/file.pdf")
    
    def test_validate_files_success(self):
        """Test validating files that exist."""
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f1:
            pptx_path = f1.name
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f2:
            pdf_path = f2.name
        
        try:
            # Should not raise
            FileService.validate_files(pptx_path, pdf_path)
        finally:
            os.unlink(pptx_path)
            os.unlink(pdf_path)
    
    def test_validate_files_pptx_missing(self):
        """Test validating with missing PPTX."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name
        
        try:
            with pytest.raises(ProcessingError, match="PPTX file not found"):
                FileService.validate_files("/nonexistent.pptx", pdf_path)
        finally:
            os.unlink(pdf_path)
    
    def test_validate_files_pdf_missing(self):
        """Test validating with missing PDF."""
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
            pptx_path = f.name
        
        try:
            with pytest.raises(ProcessingError, match="PDF file not found"):
                FileService.validate_files(pptx_path, "/nonexistent.pdf")
        finally:
            os.unlink(pptx_path)
    
    def test_create_output_directory(self):
        """Test creating output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "output", "subdir")
            
            FileService.create_output_directory(new_dir)
            
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)
    
    def test_needs_vba_restoration_true(self):
        """Test VBA restoration check returns True."""
        result = FileService._needs_vba_restoration(
            "/path/to/source.pptm",
            "/path/to/output.pptm"
        )
        assert result is True
    
    def test_needs_vba_restoration_false_source(self):
        """Test VBA restoration check returns False for non-pptm source."""
        result = FileService._needs_vba_restoration(
            "/path/to/source.pptx",
            "/path/to/output.pptm"
        )
        assert result is False
    
    def test_needs_vba_restoration_false_output(self):
        """Test VBA restoration check returns False for non-pptm output."""
        result = FileService._needs_vba_restoration(
            "/path/to/source.pptm",
            "/path/to/output.pptx"
        )
        assert result is False
    
    def test_save_presentation_basic(self):
        """Test saving presentation without VBA."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.pptx")
            
            mock_prs = Mock()
            mock_prs.slide_width = 10
            mock_prs.slide_height = 5.625
            
            with patch('services.file_service.ensure_pptx_path') as mock_ensure:
                mock_ensure.return_value = output_path
                
                result = FileService.save_presentation(
                    prs=mock_prs,
                    output_path=output_path
                )
                
                assert result == output_path
                mock_prs.save.assert_called_once()
    
    def test_save_presentation_with_aspect_ratio(self):
        """Test saving presentation with forced aspect ratio."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.pptx")
            
            mock_prs = Mock()
            
            with patch('services.file_service.ensure_pptx_path') as mock_ensure:
                with patch('services.file_service.Inches') as mock_inches:
                    mock_ensure.return_value = output_path
                    mock_inches.return_value = 10
                    
                    FileService.save_presentation(
                        prs=mock_prs,
                        output_path=output_path,
                        force_aspect_ratio=True
                    )
                    
                    # Should set slide dimensions
                    assert mock_prs.slide_width is not None
                    assert mock_prs.slide_height is not None
    
    def test_get_slide_count(self):
        """Test getting slide count."""
        with patch('services.file_service.FileService.load_presentation') as mock_load_prs:
            with patch('services.file_service.FileService.load_pdf') as mock_load_pdf:
                mock_prs = Mock()
                mock_prs.slides = [Mock(), Mock(), Mock()]
                mock_load_prs.return_value = mock_prs
                
                mock_pdf = Mock()
                mock_pdf.__len__ = Mock(return_value=5)
                mock_pdf.close = Mock()
                mock_load_pdf.return_value = mock_pdf
                
                count = FileService.get_slide_count(
                    pptx_path="/path/to/test.pptx",
                    pdf_path="/path/to/test.pdf"
                )
                
                # Should return minimum
                assert count == 3
                mock_pdf.close.assert_called_once()
