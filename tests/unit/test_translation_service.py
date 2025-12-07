"""Tests for TranslationService."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from PIL import Image

from services.translation_service import TranslationService
from utils.error_handling import TranslationError


class TestTranslationService:
    """Tests for TranslationService class."""
    
    def test_initialization(self):
        """Test service initialization."""
        translator = Mock()
        img_translator = Mock()
        
        service = TranslationService(
            translator_agent=translator,
            image_translator_agent=img_translator
        )
        
        assert service.translator_agent == translator
        assert service.image_translator_agent == img_translator
    
    @pytest.mark.asyncio
    async def test_translate_notes_success(self, mock_agent):
        """Test successful notes translation."""
        with patch('services.translation_service.run_stateless_agent') as mock_run:
            mock_run.return_value = "翻译的笔记"
            
            service = TranslationService(translator_agent=mock_agent)
            
            result = await service.translate_notes(
                english_notes="English notes",
                target_language="zh-CN",
                slide_idx=1
            )
            
            assert result == "翻译的笔记"
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_translate_notes_no_agent(self):
        """Test translation without agent raises error."""
        service = TranslationService(translator_agent=None)
        
        with pytest.raises(TranslationError, match="not available"):
            await service.translate_notes(
                english_notes="English notes",
                target_language="zh-CN"
            )
    
    @pytest.mark.asyncio
    async def test_translate_notes_empty_input(self, mock_agent):
        """Test translation with empty input raises error."""
        service = TranslationService(translator_agent=mock_agent)
        
        with pytest.raises(TranslationError, match="No English notes"):
            await service.translate_notes(
                english_notes="",
                target_language="zh-CN"
            )
    
    @pytest.mark.asyncio
    async def test_translate_notes_empty_result(self, mock_agent):
        """Test translation with empty result raises error."""
        with patch('services.translation_service.run_stateless_agent') as mock_run:
            mock_run.return_value = ""
            
            service = TranslationService(translator_agent=mock_agent)
            
            with pytest.raises(TranslationError, match="empty result"):
                await service.translate_notes(
                    english_notes="English notes",
                    target_language="zh-CN"
                )
    
    @pytest.mark.asyncio
    async def test_translate_visual_success(self, mock_agent, sample_image):
        """Test successful visual translation."""
        with patch('services.translation_service.run_visual_agent') as mock_run:
            mock_run.return_value = b"image_bytes"
            
            service = TranslationService(image_translator_agent=mock_agent)
            
            result = await service.translate_visual(
                english_visual=sample_image,
                target_language="zh-CN",
                speaker_notes="Notes",
                slide_idx=1
            )
            
            assert result == b"image_bytes"
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_translate_visual_no_agent(self, sample_image):
        """Test visual translation without agent returns None."""
        service = TranslationService(image_translator_agent=None)
        
        result = await service.translate_visual(
            english_visual=sample_image,
            target_language="zh-CN",
            speaker_notes="Notes"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_translate_visual_failure(self, mock_agent, sample_image):
        """Test visual translation failure returns None."""
        with patch('services.translation_service.run_visual_agent') as mock_run:
            mock_run.return_value = None
            
            service = TranslationService(image_translator_agent=mock_agent)
            
            result = await service.translate_visual(
                english_visual=sample_image,
                target_language="zh-CN",
                speaker_notes="Notes",
                slide_idx=1
            )
            
            assert result is None
    
    def test_is_translation_available(self, mock_agent):
        """Test translation availability check."""
        service_with = TranslationService(translator_agent=mock_agent)
        service_without = TranslationService(translator_agent=None)
        
        assert service_with.is_translation_available() is True
        assert service_without.is_translation_available() is False
    
    def test_is_visual_translation_available(self, mock_agent):
        """Test visual translation availability check."""
        service_with = TranslationService(image_translator_agent=mock_agent)
        service_without = TranslationService(image_translator_agent=None)
        
        assert service_with.is_visual_translation_available() is True
        assert service_without.is_visual_translation_available() is False
    
    @pytest.mark.asyncio
    async def test_translate_notes_with_slide_idx(self, mock_agent):
        """Test translation includes slide index in logging."""
        with patch('services.translation_service.run_stateless_agent') as mock_run:
            mock_run.return_value = "Translated"
            
            service = TranslationService(translator_agent=mock_agent)
            
            result = await service.translate_notes(
                english_notes="English",
                target_language="zh-CN",
                slide_idx=5
            )
            
            assert result == "Translated"
    
    @pytest.mark.asyncio
    async def test_language_name_mapping(self, mock_agent):
        """Test that language names are properly mapped."""
        with patch('services.translation_service.run_stateless_agent') as mock_run:
            mock_run.return_value = "Translated"
            
            service = TranslationService(translator_agent=mock_agent)
            
            await service.translate_notes(
                english_notes="English",
                target_language="zh-CN"
            )
            
            # Check that the prompt includes the language name
            call_args = mock_run.call_args[0]
            prompt = call_args[1]
            assert "Simplified Chinese" in prompt or "简体中文" in prompt
