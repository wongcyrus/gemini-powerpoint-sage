"""Constants and configuration values for Gemini Powerpoint Sage."""

from typing import Final


class ModelConfig:
    """AI model configuration."""
    
    SUPERVISOR: Final[str] = "gemini-2.5-flash"
    ANALYST: Final[str] = "gemini-3-pro-preview"
    WRITER: Final[str] = "gemini-2.5-flash"
    AUDITOR: Final[str] = "gemini-2.5-flash"
    OVERVIEWER: Final[str] = "gemini-3-pro-preview"
    DESIGNER: Final[str] = "gemini-3-pro-image-preview"
    TRANSLATOR: Final[str] = "gemini-2.5-flash"
    IMAGE_TRANSLATOR: Final[str] = "gemini-3-pro-image-preview"
    VIDEO_GENERATOR: Final[str] = "gemini-2.5-flash"
    REFINER: Final[str] = "gemini-2.5-flash"
    PROMPT_REWRITER: Final[str] = "gemini-2.5-flash"
    FALLBACK_IMAGEN: Final[str] = "imagen-4.0-generate-001"


class ProcessingConfig:
    """Processing behavior configuration."""
    
    MAX_RETRIES: Final[int] = 3
    RETRY_DELAY: Final[float] = 2.0
    RETRY_BACKOFF_MULTIPLIER: Final[float] = 2.0
    MAX_CONCURRENT_SLIDES: Final[int] = 3
    PROGRESS_SAVE_INTERVAL: Final[int] = 1  # Save after every N slides
    PDF_DPI_STANDARD: Final[int] = 150
    PDF_DPI_LOW: Final[int] = 75


class FilePatterns:
    """File naming patterns."""
    
    PROGRESS_FILE: Final[str] = "{base}_{lang}_progress.json"
    NOTES_OUTPUT: Final[str] = "{base}_{lang}_with_notes{ext}"
    VISUALS_OUTPUT: Final[str] = "{base}_{lang}_with_visuals{ext}"
    VISUALS_DIR: Final[str] = "{base}_{lang}_visuals"
    VIDEOS_DIR: Final[str] = "{base}_{lang}_videos"
    VIDEO_PROMPT_FILE: Final[str] = "slide_{idx}_video_prompt.txt"
    REIMAGINED_SLIDE: Final[str] = "slide_{idx}_reimagined.png"


class LanguageConfig:
    """Language and locale configuration."""
    
    DEFAULT_LANGUAGE: Final[str] = "en"
    
    LOCALE_NAMES: Final[dict[str, str]] = {
        "en": "English",
        "zh-CN": "Simplified Chinese (简体中文)",
        "zh-TW": "Traditional Chinese (繁體中文)",
        "yue-HK": "Cantonese (廣東話)",
        "es": "Spanish (Español)",
        "fr": "French (Français)",
        "ja": "Japanese (日本語)",
        "ko": "Korean (한국어)",
        "de": "German (Deutsch)",
        "it": "Italian (Italiano)",
        "pt": "Portuguese (Português)",
        "ru": "Russian (Русский)",
        "ar": "Arabic (العربية)",
        "hi": "Hindi (हिन्दी)",
        "th": "Thai (ไทย)",
        "vi": "Vietnamese (Tiếng Việt)",
    }
    
    @classmethod
    def get_language_name(cls, locale: str) -> str:
        """Get display name for a locale code."""
        return cls.LOCALE_NAMES.get(locale, locale)


class SlideConfig:
    """Slide and presentation configuration."""
    
    SLIDE_WIDTH_INCHES: Final[float] = 10.0
    SLIDE_HEIGHT_INCHES: Final[float] = 5.625
    ASPECT_RATIO: Final[str] = "16:9"


class EnvironmentVars:
    """Environment variable names."""
    
    PROGRESS_FILE: Final[str] = "SPEAKER_NOTE_PROGRESS_FILE"
    RETRY_ERRORS: Final[str] = "SPEAKER_NOTE_RETRY_ERRORS"
    GOOGLE_CLOUD_LOCATION: Final[str] = "GOOGLE_CLOUD_LOCATION"
    GOOGLE_CLOUD_PROJECT: Final[str] = "GOOGLE_CLOUD_PROJECT"
    FORCE_FALLBACK_IMAGE_GEN: Final[str] = "FORCE_FALLBACK_IMAGE_GEN"
    FALLBACK_IMAGEN_MODEL: Final[str] = "FALLBACK_IMAGEN_MODEL"
