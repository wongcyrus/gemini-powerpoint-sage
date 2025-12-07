"""Translation service for multi-language support."""

import logging
from typing import Optional

from PIL import Image
from google.adk.agents import LlmAgent

from config.constants import LanguageConfig
from utils.agent_utils import run_stateless_agent, run_visual_agent
from utils.error_handling import TranslationError

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating speaker notes and visuals."""
    
    def __init__(
        self,
        translator_agent: Optional[LlmAgent] = None,
        image_translator_agent: Optional[LlmAgent] = None,
    ):
        """
        Initialize translation service.
        
        Args:
            translator_agent: Agent for translating text
            image_translator_agent: Agent for translating visuals
        """
        self.translator_agent = translator_agent
        self.image_translator_agent = image_translator_agent
    
    async def translate_notes(
        self,
        english_notes: str,
        target_language: str,
        slide_idx: Optional[int] = None,
    ) -> str:
        """
        Translate speaker notes to target language.
        
        Args:
            english_notes: English speaker notes
            target_language: Target language locale code
            slide_idx: Optional slide index for logging
            
        Returns:
            Translated notes
            
        Raises:
            TranslationError: If translation fails
        """
        if not self.translator_agent:
            raise TranslationError("Translator agent not available")
        
        if not english_notes or not english_notes.strip():
            raise TranslationError("No English notes provided")
        
        lang_name = LanguageConfig.get_language_name(target_language)
        
        prompt = (
            f"Translate the following English speaker notes to {lang_name}. "
            f"Maintain technical accuracy, educational tone, and clarity. "
            f"Preserve formatting and structure.\n\n"
            f"English notes:\n{english_notes}\n\n"
            f"IMPORTANT: Provide ONLY the translated speaker notes "
            f"in {lang_name}. Do not include explanations or metadata."
        )
        
        try:
            result = await run_stateless_agent(
                self.translator_agent, prompt
            )
            
            if result and result.strip():
                if slide_idx:
                    logger.info(
                        f"Successfully translated slide {slide_idx} "
                        f"to {target_language}"
                    )
                return result.strip()
            else:
                raise TranslationError("Translation returned empty result")
                
        except Exception as e:
            error_msg = f"Translation failed: {e}"
            if slide_idx:
                error_msg = f"Slide {slide_idx}: {error_msg}"
            logger.error(error_msg, exc_info=True)
            raise TranslationError(error_msg) from e
    
    async def translate_visual(
        self,
        english_visual: Image.Image,
        target_language: str,
        speaker_notes: str,
        slide_idx: Optional[int] = None,
    ) -> Optional[bytes]:
        """
        Translate visual from English to target language.
        
        Args:
            english_visual: English slide visual
            target_language: Target language locale code
            speaker_notes: Translated speaker notes for context
            slide_idx: Optional slide index for logging
            
        Returns:
            Image bytes of translated visual or None if failed
        """
        if not self.image_translator_agent:
            logger.warning("Image translator agent not available")
            return None
        
        lang_name = LanguageConfig.get_language_name(target_language)
        
        # Build translation prompt
        design_prompt = (
            f"Translate this English slide visual to {lang_name}.\n\n"
            f"IMPORTANT:\n"
            f"- Translate ALL text to {lang_name}\n"
            f"- Keep the exact same layout and structure\n"
            f"- Ensure text is readable and fits within "
            f"the original text areas\n"
            f"- Do NOT change colors, fonts, or design\n"
            f"- Do NOT add or remove elements\n\n"
            f"Speaker Notes: {speaker_notes}"
        )
        
        try:
            img_bytes = await run_visual_agent(
                self.image_translator_agent,
                design_prompt,
                images=[english_visual]
            )
            
            if img_bytes:
                if slide_idx:
                    logger.info(
                        f"Successfully translated visual for slide {slide_idx} "
                        f"to {target_language}"
                    )
                return img_bytes
            else:
                logger.warning(
                    f"Visual translation returned no image "
                    f"for slide {slide_idx}"
                )
                return None
                
        except Exception as e:
            error_msg = f"Visual translation failed: {e}"
            if slide_idx:
                error_msg = f"Slide {slide_idx}: {error_msg}"
            logger.error(error_msg, exc_info=True)
            return None
    
    def is_translation_available(self) -> bool:
        """Check if translation is available."""
        return self.translator_agent is not None
    
    def is_visual_translation_available(self) -> bool:
        """Check if visual translation is available."""
        return self.image_translator_agent is not None
