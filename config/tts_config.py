"""TTS system configuration management."""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from core.domain.tts import TTSEngineType, VoiceConfig

logger = logging.getLogger(__name__)


@dataclass
class GeminiTTSConfig:
    """Configuration for Gemini TTS engine."""
    
    model_id: str = "gemini-2.5-flash-tts"
    pro_model_id: str = "gemini-2.5-pro-tts"
    supported_languages: Set[str] = field(default_factory=lambda: {
        "en-US", "en-IN", "ja-JP", "ko-KR", "fr-FR", 
        "de-DE", "es-ES", "it-IT", "pt-BR", "ru-RU",
        "hi-IN", "ar-EG", "nl-NL", "pl-PL", "ro-RO",
        "bn-BD", "id-ID", "mr-IN", "ta-IN", "te-IN", 
        "th-TH", "tr-TR", "uk-UA", "vi-VN", "cmn-CN", "cmn-TW"
    })
    voice_mapping: Dict[str, List[str]] = field(default_factory=lambda: {
        "en-US": ["Aoede", "Callirrhoe", "Kore", "Zephyr"],
        "en-IN": ["Leda", "Pulcherrima", "Vindemiatrix"],
        "ja-JP": ["Despina", "Erinome", "Laomedeia"],
        "ko-KR": ["Gacrux", "Sulafat"],
        "fr-FR": ["Autonoe", "Achernar"],
        "de-DE": ["Charon", "Fenrir", "Iapetus"],
        "es-ES": ["Orus", "Puck", "Umbriel"],
        "it-IT": ["Enceladus", "Achird"],
        "pt-BR": ["Algenib", "Algieba"],
        "ru-RU": ["Alnilam", "Rasalgethi"],
        "hi-IN": ["Sadachbia", "Schedar"],
        "ar-EG": ["Sadaltager", "Zubenelgenubi"],
        "nl-NL": ["Achernar", "Autonoe"],
        "pl-PL": ["Charon", "Fenrir"],
        "ro-RO": ["Iapetus", "Orus"],
        # Chinese languages (Preview) - using same voices as English for now
        "cmn-CN": ["Aoede", "Callirrhoe", "Kore", "Zephyr"],
        "cmn-TW": ["Aoede", "Callirrhoe", "Kore", "Zephyr"]
    })
    max_retries: int = 3
    timeout_seconds: int = 90  # Increased from 30 to handle complex prompts and network latency
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if language is supported by Gemini TTS."""
        return language_code in self.supported_languages
    
    def get_voices_for_language(self, language_code: str) -> List[str]:
        """Get available voices for a language."""
        return self.voice_mapping.get(language_code, self.voice_mapping.get("en-US", []))


@dataclass
class TraditionalTTSConfig:
    """Configuration for Traditional Google TTS engine."""
    
    # Language mapping from user-friendly codes to actual TTS codes
    language_mapping: Dict[str, str] = field(default_factory=lambda: {
        "zh-CN": "cmn-CN",  # Chinese Simplified -> Mandarin China
        "zh-TW": "cmn-TW",  # Chinese Traditional -> Mandarin Taiwan
        "zh-HK": "yue-HK",  # Chinese Hong Kong -> Cantonese Hong Kong
        "yue-HK": "yue-HK"  # Cantonese Hong Kong (no mapping needed)
    })
    
    fallback_languages: Set[str] = field(default_factory=lambda: {
        "yue-HK", "zh-HK", "zh-CN", "zh-TW"
    })
    
    voice_mapping: Dict[str, List[str]] = field(default_factory=lambda: {
        # Chirp 3: HD voices for English (fallback from Gemini TTS)
        "en-US": ["en-us-Chirp3-HD-Aoede", "en-us-Chirp3-HD-Callirrhoe", "en-us-Chirp3-HD-Kore", "en-us-Chirp3-HD-Zephyr"],
        # Traditional TTS voices for Chinese languages
        "yue-HK": ["yue-HK-Standard-A", "yue-HK-Standard-B", "yue-HK-Standard-C", "yue-HK-Standard-D"],
        "cmn-CN": ["cmn-CN-Standard-A", "cmn-CN-Standard-B", "cmn-CN-Standard-C", "cmn-CN-Standard-D"],
        "cmn-TW": ["cmn-TW-Standard-A", "cmn-TW-Standard-B", "cmn-TW-Standard-C", "cmn-TW-Standard-D"]
    })
    max_retries: int = 3
    timeout_seconds: int = 90  # Increased from 30 to handle complex prompts and network latency
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if language requires traditional TTS as primary engine."""
        # Traditional TTS is primary for Chinese languages only
        # English (en-US) is available as fallback but not primary
        return language_code in self.fallback_languages
    
    def can_handle_language(self, language_code: str) -> bool:
        """Check if language can be handled by traditional TTS (including fallback)."""
        # Traditional TTS can handle fallback languages + any language with voice mapping
        return (language_code in self.fallback_languages or 
                language_code in self.voice_mapping)
    
    def map_language_code(self, language_code: str) -> str:
        """Map user-friendly language code to actual TTS language code."""
        return self.language_mapping.get(language_code, language_code)
    
    def get_voices_for_language(self, language_code: str) -> List[str]:
        """Get available voices for a language."""
        # Map to actual TTS language code first
        actual_code = self.map_language_code(language_code)
        return self.voice_mapping.get(actual_code, [])


@dataclass
class TTSCacheConfig:
    """Configuration for TTS caching system."""
    
    enabled: bool = True
    ttl_hours: int = 24
    max_cache_size_mb: int = 1000
    cache_directory: str = "cache/tts"
    metadata_file: str = "cache_metadata.json"
    
    def __post_init__(self):
        """Validate cache configuration."""
        if self.ttl_hours < 0:
            raise ValueError("TTL hours must be non-negative")
        
        if self.max_cache_size_mb <= 0:
            raise ValueError("Max cache size must be positive")


@dataclass
class TTSStorageConfig:
    """Configuration for TTS storage system."""
    
    bucket_name: str = ""
    local_cache_dir: str = "cache/speech"
    directory_pattern: str = "{base_name}_{language_code}_speech"
    filename_pattern: str = "slide_{slide_number}_{content_hash}.mp3"
    upload_timeout_seconds: int = 60
    
    def __post_init__(self):
        """Validate storage configuration."""
        # Get bucket name from environment if not provided
        if not self.bucket_name:
            self.bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET", "")
        
        if self.upload_timeout_seconds <= 0:
            raise ValueError("Upload timeout must be positive")


@dataclass
class TTSConfig:
    """Main TTS system configuration."""
    
    enabled: bool = True
    gemini: GeminiTTSConfig = field(default_factory=GeminiTTSConfig)
    traditional: TraditionalTTSConfig = field(default_factory=TraditionalTTSConfig)
    cache: TTSCacheConfig = field(default_factory=TTSCacheConfig)
    storage: TTSStorageConfig = field(default_factory=TTSStorageConfig)
    parallel_processing: bool = True
    max_concurrent_slides: int = 3
    # Engine-specific concurrency settings
    gemini_max_concurrent: int = 1  # Gemini TTS is unstable with multi-threading
    traditional_max_concurrent: int = 3  # Traditional TTS can handle more concurrency
    
    def __post_init__(self):
        """Apply environment variable overrides."""
        self._apply_env_overrides()
    
    def _apply_env_overrides(self) -> None:
        """Apply configuration from environment variables."""
        # TTS system enable/disable
        if "TTS_ENABLED" in os.environ:
            self.enabled = os.getenv("TTS_ENABLED", "true").lower() == "true"
        
        # Cache configuration
        if "TTS_CACHE_ENABLED" in os.environ:
            self.cache.enabled = os.getenv("TTS_CACHE_ENABLED", "true").lower() == "true"
        
        if "TTS_CACHE_TTL_HOURS" in os.environ:
            try:
                self.cache.ttl_hours = int(os.getenv("TTS_CACHE_TTL_HOURS", "24"))
            except ValueError:
                logger.warning("Invalid TTS_CACHE_TTL_HOURS value, using default")
        
        # Storage configuration
        if "TTS_STORAGE_BUCKET" in os.environ:
            self.storage.bucket_name = os.getenv("TTS_STORAGE_BUCKET", "")
        
        # Processing configuration
        if "TTS_PARALLEL_PROCESSING" in os.environ:
            self.parallel_processing = os.getenv("TTS_PARALLEL_PROCESSING", "true").lower() == "true"
        
        if "TTS_MAX_CONCURRENT_SLIDES" in os.environ:
            try:
                self.max_concurrent_slides = int(os.getenv("TTS_MAX_CONCURRENT_SLIDES", "3"))
            except ValueError:
                logger.warning("Invalid TTS_MAX_CONCURRENT_SLIDES value, using default")
        
        # Engine-specific concurrency settings
        if "TTS_GEMINI_MAX_CONCURRENT" in os.environ:
            try:
                self.gemini_max_concurrent = int(os.getenv("TTS_GEMINI_MAX_CONCURRENT", "1"))
            except ValueError:
                logger.warning("Invalid TTS_GEMINI_MAX_CONCURRENT value, using default")
        
        if "TTS_TRADITIONAL_MAX_CONCURRENT" in os.environ:
            try:
                self.traditional_max_concurrent = int(os.getenv("TTS_TRADITIONAL_MAX_CONCURRENT", "3"))
            except ValueError:
                logger.warning("Invalid TTS_TRADITIONAL_MAX_CONCURRENT value, using default")
        
        # Timeout configuration
        if "TTS_TIMEOUT_SECONDS" in os.environ:
            try:
                timeout_value = int(os.getenv("TTS_TIMEOUT_SECONDS", "90"))
                self.gemini.timeout_seconds = timeout_value
                self.traditional.timeout_seconds = timeout_value
                logger.info(f"TTS timeout set to {timeout_value} seconds via environment variable")
            except ValueError:
                logger.warning("Invalid TTS_TIMEOUT_SECONDS value, using default")
    
    def normalize_language_code(self, language_code: str) -> str:
        """
        Normalize language code to full locale format.
        
        Args:
            language_code: Language code (e.g., "en", "zh")
            
        Returns:
            Normalized language code (e.g., "en-US", "zh-CN")
        """
        # Common language mappings
        language_mappings = {
            "en": "en-US",
            "zh": "cmn-CN",  # Map Chinese to Mandarin for Gemini TTS
            "zh-CN": "cmn-CN",  # Map zh-CN to cmn-CN for Gemini TTS
            "zh-TW": "cmn-TW",  # Map zh-TW to cmn-TW for Gemini TTS
            "ja": "ja-JP",
            "ko": "ko-KR",
            "fr": "fr-FR",
            "de": "de-DE",
            "es": "es-ES",
            "it": "it-IT",
            "pt": "pt-BR",
            "ru": "ru-RU",
            "hi": "hi-IN",
            "ar": "ar-EG",
            "nl": "nl-NL",
            "pl": "pl-PL",
            "ro": "ro-RO"
        }
        
        # Apply mapping if found, otherwise return original
        mapped = language_mappings.get(language_code, language_code)
        return mapped
    
    def select_engine_for_language(self, language_code: str) -> TTSEngineType:
        """
        Select appropriate TTS engine based on language.
        
        Args:
            language_code: Language code (e.g., "en-US", "yue-HK")
            
        Returns:
            TTSEngineType to use for this language
        """
        # Normalize language code first
        normalized_code = self.normalize_language_code(language_code)
        
        # Check if language is supported by Gemini TTS first (preferred engine)
        if self.gemini.is_language_supported(normalized_code):
            return TTSEngineType.GEMINI
        
        # Check if language requires traditional TTS (specific languages like Cantonese)
        if self.traditional.is_language_supported(normalized_code):
            return TTSEngineType.TRADITIONAL
        
        # Check if traditional TTS can handle it as fallback
        if self.traditional.can_handle_language(normalized_code):
            return TTSEngineType.TRADITIONAL
        
        # Default fallback to traditional TTS for unsupported languages
        logger.warning(f"Language {normalized_code} not explicitly supported, falling back to traditional TTS")
        return TTSEngineType.TRADITIONAL
    
    def get_max_concurrent_for_engine(self, engine_type: TTSEngineType) -> int:
        """
        Get maximum concurrent operations for a specific TTS engine.
        
        Args:
            engine_type: The TTS engine type
            
        Returns:
            Maximum concurrent operations for the engine
        """
        if not self.parallel_processing:
            return 1
        
        if engine_type == TTSEngineType.GEMINI:
            return self.gemini_max_concurrent
        else:
            return self.traditional_max_concurrent
    
    def get_voice_config_for_language(
        self, 
        language_code: str, 
        engine_type: Optional[TTSEngineType] = None,
        gender: str = "neutral"
    ) -> VoiceConfig:
        """
        Get voice configuration for a language and engine.
        
        Args:
            language_code: Language code
            engine_type: Optional engine type (auto-selected if None)
            gender: Preferred gender ("male", "female", "neutral")
            
        Returns:
            VoiceConfig for the language and engine
        """
        # Normalize language code first
        normalized_code = self.normalize_language_code(language_code)
        
        if engine_type is None:
            engine_type = self.select_engine_for_language(language_code)
        
        # Get available voices based on engine type
        if engine_type == TTSEngineType.GEMINI:
            available_voices = self.gemini.get_voices_for_language(normalized_code)
        else:
            available_voices = self.traditional.get_voices_for_language(normalized_code)
        
        # Select voice based on gender preference
        selected_voice = self._select_voice_by_gender(available_voices, gender)
        
        return VoiceConfig(
            language_code=normalized_code,
            gender=gender,
            voice_name=selected_voice
        )
    
    def _select_voice_by_gender(self, available_voices: List[str], preferred_gender: str) -> Optional[str]:
        """Select voice based on gender preference."""
        if not available_voices:
            return None
        
        # For Gemini TTS voices, use simple heuristics
        # (In a real implementation, this would be more sophisticated)
        female_voices = {"Aoede", "Callirrhoe", "Kore", "Zephyr", "Leda", "Pulcherrima", 
                        "Vindemiatrix", "Despina", "Erinome", "Laomedeia", "Gacrux", 
                        "Sulafat", "Autonoe", "Achernar"}
        
        if preferred_gender.lower() == "female":
            female_available = [v for v in available_voices if v in female_voices]
            return female_available[0] if female_available else available_voices[0]
        elif preferred_gender.lower() == "male":
            male_available = [v for v in available_voices if v not in female_voices]
            return male_available[0] if male_available else available_voices[0]
        else:
            # Neutral - return first available
            return available_voices[0]
    
    def validate(self) -> bool:
        """
        Validate TTS configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If validation fails
        """
        if not self.enabled:
            return True  # Skip validation if TTS is disabled
        
        # Validate storage bucket is configured
        if not self.storage.bucket_name:
            raise ValueError("TTS storage bucket name must be configured")
        
        # Validate cache directory can be created
        try:
            os.makedirs(self.cache.cache_directory, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create cache directory: {e}")
        
        # Validate concurrent processing limits
        if self.max_concurrent_slides <= 0:
            raise ValueError("Max concurrent slides must be positive")
        
        if self.gemini_max_concurrent <= 0:
            raise ValueError("Gemini max concurrent must be positive")
        
        if self.traditional_max_concurrent <= 0:
            raise ValueError("Traditional max concurrent must be positive")
        
        return True
    
    def get_cache_directory(self) -> str:
        """Get full path to cache directory."""
        return os.path.abspath(self.cache.cache_directory)
    
    def get_storage_directory_pattern(self) -> str:
        """Get storage directory pattern."""
        return self.storage.directory_pattern
    
    def get_filename_pattern(self) -> str:
        """Get filename pattern for audio files."""
        return self.storage.filename_pattern


# Default TTS configuration instance
DEFAULT_TTS_CONFIG = TTSConfig()


def get_tts_config() -> TTSConfig:
    """Get TTS configuration with environment overrides."""
    return TTSConfig()


def create_tts_config_from_dict(config_dict: Dict) -> TTSConfig:
    """Create TTS configuration from dictionary."""
    # Extract nested configurations
    gemini_config = GeminiTTSConfig(**config_dict.get("gemini", {}))
    traditional_config = TraditionalTTSConfig(**config_dict.get("traditional", {}))
    cache_config = TTSCacheConfig(**config_dict.get("cache", {}))
    storage_config = TTSStorageConfig(**config_dict.get("storage", {}))
    
    # Create main config
    main_config = {k: v for k, v in config_dict.items() 
                   if k not in ["gemini", "traditional", "cache", "storage"]}
    
    return TTSConfig(
        gemini=gemini_config,
        traditional=traditional_config,
        cache=cache_config,
        storage=storage_config,
        **main_config
    )