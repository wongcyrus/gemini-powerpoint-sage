"""TTS engine selection logic."""

import logging
from typing import Optional

from core.domain.tts import TTSEngineType, VoiceConfig
from config.tts_config import TTSConfig

logger = logging.getLogger(__name__)


class EngineSelector:
    """Selects appropriate TTS engine based on language and configuration."""
    
    def __init__(self, tts_config: TTSConfig):
        """Initialize engine selector with configuration."""
        self.tts_config = tts_config
    
    def select_engine(self, language_code: str) -> TTSEngineType:
        """
        Select appropriate TTS engine based on language.
        
        Args:
            language_code: Language code (e.g., "en-US", "yue-HK")
            
        Returns:
            TTSEngineType to use for this language
        """
        return self.tts_config.select_engine_for_language(language_code)
    
    def get_voice_config(
        self,
        language_code: str,
        engine_type: Optional[TTSEngineType] = None,
        gender: str = "neutral"
    ) -> VoiceConfig:
        """
        Get voice configuration for language and engine.
        
        Args:
            language_code: Language code
            engine_type: Optional engine type (auto-selected if None)
            gender: Preferred gender ("male", "female", "neutral")
            
        Returns:
            VoiceConfig for the language and engine
        """
        return self.tts_config.get_voice_config_for_language(
            language_code, engine_type, gender
        )
    
    def is_gemini_supported(self, language_code: str) -> bool:
        """Check if language is supported by Gemini TTS."""
        return self.tts_config.gemini.is_language_supported(language_code)
    
    def is_traditional_required(self, language_code: str) -> bool:
        """Check if language requires traditional TTS."""
        return self.tts_config.traditional.is_language_supported(language_code)