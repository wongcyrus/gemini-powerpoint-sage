"""Context management service for presentations."""

import logging
import os
from typing import Optional

import pymupdf
from PIL import Image

from config.constants import ProcessingConfig
from utils.agent_utils import run_stateless_agent
from utils.progress_utils import load_progress, save_progress, get_progress_file_path
from utils.error_handling import ProcessingError

logger = logging.getLogger(__name__)


class ContextService:
    """Service for managing presentation context."""
    
    def __init__(
        self,
        overviewer_agent,
        translator_agent=None,
    ):
        """
        Initialize context service.
        
        Args:
            overviewer_agent: Agent for generating global context
            translator_agent: Optional agent for translating context
        """
        self.overviewer_agent = overviewer_agent
        self.translator_agent = translator_agent
    
    async def get_global_context(
        self,
        pdf_doc,
        limit: int,
        progress_file: str,
        language: str = "en",
        pptx_path: Optional[str] = None,
        retry_errors: bool = False,
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Get or generate global context for presentation.
        
        Args:
            pdf_doc: PDF document object
            limit: Number of slides to analyze
            progress_file: Path to progress file
            language: Target language
            pptx_path: Path to PPTX file (for English context lookup)
            retry_errors: Whether to regenerate cached context
            output_dir: Optional output directory (for finding English progress file)
            
        Returns:
            Global context string
        """
        # Load progress
        progress = load_progress(progress_file)
        
        # Check if cached
        if self._has_cached_context(progress, retry_errors):
            logger.info("Using cached global context from progress file")
            return progress["global_context"]
        
        # For non-English, try to translate from English
        if language != "en" and pptx_path:
            translated_context = await self._translate_from_english(
                pptx_path, language, output_dir
            )
            if translated_context:
                # Cache it
                progress["global_context"] = translated_context
                save_progress(progress_file, progress)
                return translated_context
        
        # Generate new context
        logger.info("--- Generating Global Context ---")
        
        all_images = self._extract_all_images(pdf_doc, limit)
        
        global_context = await run_stateless_agent(
            self.overviewer_agent,
            "Here are the slides for the entire presentation. Analyze them.",
            images=all_images
        )
        
        logger.info(f"Global Context Generated: {len(global_context)} chars")
        
        # Cache it
        progress["global_context"] = global_context
        save_progress(progress_file, progress)
        
        return global_context
    
    def load_english_notes(
        self,
        pptx_path: str,
        language: str
    ) -> dict[int, str]:
        """
        Load English notes for translation mode.
        
        Args:
            pptx_path: Path to PPTX file
            language: Target language
            
        Returns:
            Dictionary mapping slide index to English notes
        """
        if language == "en":
            return {}
        
        en_progress_file = get_progress_file_path(pptx_path, "en")
        
        if not os.path.exists(en_progress_file):
            logger.warning(
                f"English notes not found at {en_progress_file}. "
                "Translation mode will fall back to generation mode."
            )
            return {}
        
        en_progress = load_progress(en_progress_file)
        english_notes = {}
        
        for slide_data in en_progress.get("slides", {}).values():
            if slide_data.get("status") == "success":
                slide_idx = slide_data.get("slide_index")
                note = slide_data.get("note")
                if slide_idx and note:
                    english_notes[slide_idx] = note
        
        logger.info(
            f"Loaded {len(english_notes)} English notes for translation"
        )
        
        return english_notes
    
    def _has_cached_context(
        self,
        progress: dict,
        retry_errors: bool
    ) -> bool:
        """Check if valid cached context exists."""
        return (
            "global_context" in progress
            and progress["global_context"]
            and len(progress["global_context"]) > 50
            and not retry_errors
        )
    
    async def _translate_from_english(
        self,
        pptx_path: str,
        target_language: str,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        Translate global context from English.
        
        Args:
            pptx_path: Path to PPTX file
            target_language: Target language code
            output_dir: Optional output directory
            
        Returns:
            Translated context or None
        """
        if not self.translator_agent:
            return None
        
        en_progress_file = get_progress_file_path(pptx_path, "en", output_dir)
        
        if not os.path.exists(en_progress_file):
            return None
        
        en_progress = load_progress(en_progress_file)
        en_global_context = en_progress.get("global_context")
        
        if not en_global_context or len(en_global_context) < 50:
            return None
        
        logger.info("--- Translating Global Context from English ---")
        
        from config.constants import LanguageConfig
        lang_name = LanguageConfig.get_language_name(target_language)
        
        # Add Chinese locale specific instructions
        chinese_instruction = ""
        if target_language == "zh-CN":
            chinese_instruction = (
                f"\n\nCHINESE LOCALE REQUIREMENT: "
                f"You MUST use ONLY Simplified Chinese characters (简体中文). "
                f"Examples: Use 网络 (not 網絡), 数据 (not 數據), 计算机 (not 計算機)."
            )
        elif target_language in ["zh-TW", "zh-HK", "yue-HK"]:
            chinese_instruction = (
                f"\n\nCHINESE LOCALE REQUIREMENT: "
                f"You MUST use ONLY Traditional Chinese characters (繁體中文). "
                f"Examples: Use 網絡 (not 网络), 數據 (not 数据), 計算機 (not 计算机)."
            )
        
        # Use styled translation for global context
        translate_prompt = (
            f"Translate the following presentation overview to {lang_name}. "
            f"Apply the configured speaker style and adapt cultural references appropriately. "
            f"Maintain the narrative structure and key vocabulary while ensuring the content "
            f"sounds natural and engaging in {lang_name}.\n\n"
            f"PRESENTATION OVERVIEW:\n{en_global_context}\n\n"
            f"IMPORTANT: Provide ONLY the translated overview in {lang_name}. "
            f"Do not include explanations or metadata.{chinese_instruction}"
        )
        
        try:
            global_context = await run_stateless_agent(
                self.translator_agent,
                translate_prompt
            )
            
            logger.info(
                f"Global Context Translated: {len(global_context)} chars"
            )
            
            return global_context
        except Exception as e:
            logger.error(f"Failed to translate global context: {e}")
            return None
    
    def _extract_all_images(
        self,
        pdf_doc,
        limit: int
    ) -> list[Image.Image]:
        """
        Extract all slide images from PDF.
        
        Args:
            pdf_doc: PDF document object
            limit: Number of slides to extract
            
        Returns:
            List of PIL Images
        """
        all_images = []
        
        for i in range(limit):
            pix = pdf_doc[i].get_pixmap(dpi=ProcessingConfig.PDF_DPI_LOW)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            all_images.append(img)
        
        return all_images
