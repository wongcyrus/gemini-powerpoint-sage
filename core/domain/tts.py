"""TTS domain entities and data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from pathlib import Path


class TTSEngineType(Enum):
    """TTS engine types for dual-engine system."""
    
    GEMINI = "gemini"
    TRADITIONAL = "traditional"


class PresentationType(Enum):
    """Presentation types for style context."""
    
    BUSINESS = "business"
    ACADEMIC = "academic"
    TRAINING = "training"
    TECHNICAL = "technical"
    NARRATIVE = "narrative"
    CASUAL = "casual"


@dataclass
class VoiceConfig:
    """Voice configuration for TTS engines."""
    
    language_code: str
    gender: str = "neutral"  # "male", "female", "neutral"
    speaking_rate: float = 1.0  # 0.25 to 4.0
    pitch: float = 0.0  # -20.0 to 20.0
    volume_gain_db: float = 0.0  # -96.0 to 16.0
    voice_name: Optional[str] = None  # Specific voice name if available
    
    def __post_init__(self):
        """Validate voice configuration."""
        if not (0.25 <= self.speaking_rate <= 4.0):
            raise ValueError("Speaking rate must be between 0.25 and 4.0")
        
        if not (-20.0 <= self.pitch <= 20.0):
            raise ValueError("Pitch must be between -20.0 and 20.0")
        
        if not (-96.0 <= self.volume_gain_db <= 16.0):
            raise ValueError("Volume gain must be between -96.0 and 16.0")
        
        if self.gender not in ["male", "female", "neutral"]:
            raise ValueError("Gender must be 'male', 'female', or 'neutral'")


@dataclass
class StyleContext:
    """Style context for TTS generation."""
    
    tone: str = "professional"  # professional, casual, enthusiastic, technical, narrative
    pace: str = "normal"  # slow, normal, fast
    emphasis_words: List[str] = field(default_factory=list)
    emotional_indicators: List[str] = field(default_factory=list)
    presentation_type: PresentationType = PresentationType.BUSINESS
    confidence_score: float = 0.5  # 0.0 to 1.0 confidence in style analysis
    
    def __post_init__(self):
        """Validate style context."""
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        valid_tones = ["professional", "casual", "enthusiastic", "technical", "narrative"]
        if self.tone not in valid_tones:
            raise ValueError(f"Tone must be one of: {valid_tones}")
        
        valid_paces = ["slow", "normal", "fast"]
        if self.pace not in valid_paces:
            raise ValueError(f"Pace must be one of: {valid_paces}")


@dataclass
class TTSResult:
    """Result of TTS generation."""
    
    audio_data: Optional[bytes] = None
    public_url: str = ""
    cache_key: str = ""
    file_path: str = ""
    duration_seconds: float = 0.0
    engine_used: TTSEngineType = TTSEngineType.GEMINI
    style_prompt: str = ""
    voice_config: Optional[VoiceConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if result contains valid audio data."""
        return (self.audio_data is not None and len(self.audio_data) > 0) or bool(self.public_url)
    
    def has_file(self) -> bool:
        """Check if result has a file path."""
        return bool(self.file_path) and Path(self.file_path).exists()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "public_url": self.public_url,
            "cache_key": self.cache_key,
            "file_path": self.file_path,
            "duration_seconds": self.duration_seconds,
            "engine_used": self.engine_used.value,
            "style_prompt": self.style_prompt,
            "voice_config": self.voice_config.__dict__ if self.voice_config else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TTSResult":
        """Create from dictionary."""
        voice_config = None
        if data.get("voice_config"):
            voice_config = VoiceConfig(**data["voice_config"])
        
        return cls(
            public_url=data.get("public_url", ""),
            cache_key=data.get("cache_key", ""),
            file_path=data.get("file_path", ""),
            duration_seconds=data.get("duration_seconds", 0.0),
            engine_used=TTSEngineType(data.get("engine_used", "gemini")),
            style_prompt=data.get("style_prompt", ""),
            voice_config=voice_config,
            metadata=data.get("metadata", {})
        )


@dataclass
class SlideData:
    """Data for slide processing in TTS system."""
    
    slide_number: int
    text_content: str
    speaker_notes: str = ""
    language_code: str = "en-US"
    presentation_id: str = ""
    title: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate slide data."""
        if self.slide_number < 1:
            raise ValueError("Slide number must be positive")
        
        if not self.text_content.strip():
            raise ValueError("Text content cannot be empty")
    
    def get_combined_text(self) -> str:
        """Get combined text content including speaker notes."""
        parts = []
        
        if self.title.strip():
            parts.append(f"Title: {self.title}")
        
        if self.text_content.strip():
            parts.append(f"Content: {self.text_content}")
        
        if self.speaker_notes.strip():
            parts.append(f"Notes: {self.speaker_notes}")
        
        return "\n\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "slide_number": self.slide_number,
            "text_content": self.text_content,
            "speaker_notes": self.speaker_notes,
            "language_code": self.language_code,
            "presentation_id": self.presentation_id,
            "title": self.title,
            "metadata": self.metadata
        }


@dataclass
class AudioResult:
    """Audio processing result with metadata."""
    
    audio_data: bytes
    public_url: str = ""
    cache_key: str = ""
    file_path: str = ""
    duration_seconds: float = 0.0
    engine_used: TTSEngineType = TTSEngineType.GEMINI
    style_prompt: str = ""
    
    def __post_init__(self):
        """Validate audio result."""
        if not self.audio_data or len(self.audio_data) == 0:
            raise ValueError("Audio data cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "public_url": self.public_url,
            "cache_key": self.cache_key,
            "file_path": self.file_path,
            "duration_seconds": self.duration_seconds,
            "engine_used": self.engine_used.value,
            "style_prompt": self.style_prompt
        }
    
    def to_tts_result(self, voice_config: Optional[VoiceConfig] = None) -> TTSResult:
        """Convert to TTSResult."""
        return TTSResult(
            audio_data=self.audio_data,
            public_url=self.public_url,
            cache_key=self.cache_key,
            file_path=self.file_path,
            duration_seconds=self.duration_seconds,
            engine_used=self.engine_used,
            style_prompt=self.style_prompt,
            voice_config=voice_config
        )


class TTSEngineError(Exception):
    """Exception raised by TTS engines."""
    
    def __init__(self, message: str, engine_type: Optional[TTSEngineType] = None):
        super().__init__(message)
        self.engine_type = engine_type


class TTSCacheError(Exception):
    """Exception raised by TTS cache operations."""
    pass


class TTSStorageError(Exception):
    """Exception raised by TTS storage operations."""
    pass