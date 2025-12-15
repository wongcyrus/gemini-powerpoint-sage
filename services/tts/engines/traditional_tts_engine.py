"""Traditional Google TTS engine implementation for Cantonese and fallback scenarios."""

import logging
from typing import Optional, List, Dict, Any
import asyncio
import xml.etree.ElementTree as ET

from google.cloud import texttospeech
from google.api_core import exceptions as gcp_exceptions

from core.domain.tts import (
    TTSEngineType, VoiceConfig, StyleContext, TTSResult, TTSEngineError
)
from config.tts_config import TraditionalTTSConfig
from utils.text_processing import strip_markdown

logger = logging.getLogger(__name__)


class TraditionalTTSEngine:
    """
    Traditional Google TTS engine for Cantonese and fallback scenarios.
    
    Uses Google Cloud Text-to-Speech API with SSML enhancement
    for languages not supported by Gemini TTS, particularly Cantonese (yue-HK).
    """
    
    def __init__(self, client: texttospeech.TextToSpeechClient, config: TraditionalTTSConfig):
        """
        Initialize Traditional TTS engine.
        
        Args:
            client: Google Cloud Text-to-Speech client
            config: Traditional TTS configuration
        """
        self.client = client
        self.config = config
        
        # Voice mapping for traditional TTS languages
        self.VOICE_MAPPING = config.voice_mapping
    
    async def synthesize_speech(
        self,
        text: str,
        voice_config: VoiceConfig,
        language_code: str,
        style_context: Optional[StyleContext] = None
    ) -> TTSResult:
        """
        Synthesize speech using traditional Google TTS.
        
        Args:
            text: Text content to synthesize
            voice_config: Voice configuration parameters
            language_code: Target language code
            style_context: Optional style context for SSML enhancement
            
        Returns:
            AudioResult with generated audio data
            
        Raises:
            TTSEngineError: If synthesis fails
        """
        try:
            # Strip markdown from text first
            clean_text = strip_markdown(text)
            
            # Enhance text with SSML if style context is provided
            enhanced_text = self._enhance_text_with_ssml(clean_text, style_context) if style_context else clean_text
            
            # Build the synthesis request
            request = self._build_synthesis_request(
                enhanced_text, voice_config, language_code
            )
            
            logger.info(f"Synthesizing speech with Traditional TTS for language {language_code}")
            if style_context:
                logger.debug(f"Using SSML enhancement for tone: {style_context.tone}")
            
            # Call Traditional TTS API with retry logic
            response = await self._call_tts_api_with_retry(request)
            
            # Validate and process audio response
            if not response.audio_content:
                raise TTSEngineError("Empty audio content received from Traditional TTS", TTSEngineType.TRADITIONAL)
            
            # Validate MP3 format (reuse validation from Gemini engine)
            if not self._validate_mp3_format(response.audio_content):
                raise TTSEngineError("Generated audio is not valid MP3 format", TTSEngineType.TRADITIONAL)
            
            # Extract audio duration
            duration = self._extract_audio_duration(response.audio_content, clean_text)
            
            return TTSResult(
                audio_data=response.audio_content,
                duration_seconds=duration,
                engine_used=TTSEngineType.TRADITIONAL,
                style_prompt=self._create_style_description(style_context) if style_context else ""
            )
            
        except Exception as e:
            logger.error(f"Traditional TTS synthesis failed for language {language_code}: {e}")
            raise TTSEngineError(f"Traditional TTS failed: {e}", TTSEngineType.TRADITIONAL)
    
    def _build_synthesis_request(
        self,
        text: str,
        voice_config: VoiceConfig,
        language_code: str
    ) -> texttospeech.SynthesizeSpeechRequest:
        """
        Build Traditional TTS synthesis request.
        
        Args:
            text: Text to synthesize (may include SSML)
            voice_config: Voice configuration
            language_code: Target language
            
        Returns:
            Configured synthesis request
        """
        # Map language code to actual TTS language code
        actual_language_code = self.config.map_language_code(language_code)
        
        # Select appropriate voice for the actual language code
        available_voices = self.VOICE_MAPPING.get(actual_language_code, [])
        selected_voice = self._select_voice(available_voices, voice_config.gender)
        
        # Build voice selection using the actual language code
        # For Traditional TTS, don't specify model_name (only Gemini TTS uses it)
        voice = texttospeech.VoiceSelectionParams(
            language_code=actual_language_code,
            name=selected_voice or voice_config.voice_name,
            ssml_gender=self._get_ssml_gender(voice_config.gender)
        )
        
        # Build audio configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=voice_config.speaking_rate,
            pitch=voice_config.pitch,
            volume_gain_db=voice_config.volume_gain_db
        )
        
        # Determine if text contains SSML
        is_ssml = text.strip().startswith('<speak>') and text.strip().endswith('</speak>')
        
        # Build synthesis input
        if is_ssml:
            synthesis_input = texttospeech.SynthesisInput(ssml=text)
        else:
            synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Create the request
        return texttospeech.SynthesizeSpeechRequest(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
    
    async def _call_tts_api_with_retry(
        self, 
        request: texttospeech.SynthesizeSpeechRequest
    ) -> texttospeech.SynthesizeSpeechResponse:
        """
        Call TTS API with exponential backoff retry.
        
        Args:
            request: Synthesis request
            
        Returns:
            TTS response
            
        Raises:
            TTSEngineError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Use asyncio timeout for the request
                response = await asyncio.wait_for(
                    self._async_synthesize_speech(request),
                    timeout=self.config.timeout_seconds
                )
                
                logger.debug(f"Traditional TTS synthesis successful on attempt {attempt + 1}")
                return response
                
            except (gcp_exceptions.GoogleAPIError, asyncio.TimeoutError) as e:
                last_exception = e
                wait_time = 2 ** attempt  # Exponential backoff
                
                logger.warning(
                    f"Traditional TTS attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {wait_time} seconds..."
                )
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(wait_time)
        
        # All retries failed
        raise TTSEngineError(
            f"Traditional TTS failed after {self.config.max_retries} attempts: {last_exception}",
            TTSEngineType.TRADITIONAL
        )
    
    async def _async_synthesize_speech(
        self, 
        request: texttospeech.SynthesizeSpeechRequest
    ) -> texttospeech.SynthesizeSpeechResponse:
        """
        Async wrapper for TTS client synthesis.
        
        Args:
            request: Synthesis request
            
        Returns:
            TTS response
        """
        # Run the synchronous TTS call in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.client.synthesize_speech,
            request
        )
    
    def _enhance_text_with_ssml(self, text: str, style_context: StyleContext) -> str:
        """
        Enhance text with SSML tags based on style context.
        
        Args:
            text: Original text content
            style_context: Style context for enhancement
            
        Returns:
            SSML-enhanced text
        """
        # Start with speak tag
        ssml_parts = ['<speak>']
        
        # Add prosody modifications based on style context
        prosody_attrs = []
        
        # Pace control
        if style_context.pace == "slow":
            prosody_attrs.append('rate="slow"')
        elif style_context.pace == "fast":
            prosody_attrs.append('rate="fast"')
        
        # Tone-based pitch adjustments
        if style_context.tone == "enthusiastic":
            prosody_attrs.append('pitch="+2st"')  # Slightly higher pitch
        elif style_context.tone == "technical":
            prosody_attrs.append('pitch="-1st"')  # Slightly lower pitch for authority
        
        # Volume adjustments for presentation types
        if style_context.presentation_type.value == "training":
            prosody_attrs.append('volume="medium"')
        
        # Apply prosody if we have modifications
        if prosody_attrs:
            prosody_tag = f'<prosody {" ".join(prosody_attrs)}>'
            ssml_parts.append(prosody_tag)
        
        # Process text with emphasis
        enhanced_text = self._add_emphasis_to_text(text, style_context.emphasis_words)
        ssml_parts.append(enhanced_text)
        
        # Close prosody tag if opened
        if prosody_attrs:
            ssml_parts.append('</prosody>')
        
        # Add breaks for better pacing in certain contexts
        if style_context.tone in ["technical", "training"]:
            # Add slight pauses after sentences for better comprehension
            text_with_breaks = ssml_parts[-1].replace('. ', '. <break time="300ms"/>')
            ssml_parts[-1] = text_with_breaks
        
        # Close speak tag
        ssml_parts.append('</speak>')
        
        ssml_text = ''.join(ssml_parts)
        
        # Validate SSML
        if self._validate_ssml(ssml_text):
            return ssml_text
        else:
            logger.warning("Generated SSML is invalid, falling back to plain text")
            return text
    
    def _add_emphasis_to_text(self, text: str, emphasis_words: List[str]) -> str:
        """
        Add SSML emphasis tags to specific words.
        
        Args:
            text: Original text
            emphasis_words: Words to emphasize
            
        Returns:
            Text with emphasis tags
        """
        if not emphasis_words:
            return text
        
        enhanced_text = text
        
        for word in emphasis_words:
            if word.lower() in text.lower():
                # Use case-insensitive replacement with emphasis
                import re
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                enhanced_text = pattern.sub(
                    f'<emphasis level="moderate">{word}</emphasis>',
                    enhanced_text,
                    count=1  # Only emphasize first occurrence
                )
        
        return enhanced_text
    
    def _validate_ssml(self, ssml_text: str) -> bool:
        """
        Validate SSML markup.
        
        Args:
            ssml_text: SSML text to validate
            
        Returns:
            True if valid SSML
        """
        try:
            # Parse SSML as XML to check for validity
            ET.fromstring(ssml_text)
            return True
        except ET.ParseError as e:
            logger.debug(f"SSML validation failed: {e}")
            return False
    
    def _select_voice(self, available_voices: List[str], preferred_gender: str) -> Optional[str]:
        """
        Select voice based on gender preference and availability.
        
        Args:
            available_voices: List of available voice names
            preferred_gender: Preferred gender ("male", "female", "neutral")
            
        Returns:
            Selected voice name or None if no voices available
        """
        if not available_voices:
            return None
        
        # For traditional TTS, voice names often include gender indicators
        # e.g., "yue-HK-Standard-A" (female), "yue-HK-Standard-C" (male)
        
        if preferred_gender.lower() == "female":
            # Look for voices typically associated with female (A, B in Google TTS)
            female_voices = [v for v in available_voices if v.endswith(('-A', '-B'))]
            if female_voices:
                return female_voices[0]
        elif preferred_gender.lower() == "male":
            # Look for voices typically associated with male (C, D in Google TTS)
            male_voices = [v for v in available_voices if v.endswith(('-C', '-D'))]
            if male_voices:
                return male_voices[0]
        
        # Neutral or fallback - return first available
        return available_voices[0]
    
    def _get_ssml_gender(self, gender: str) -> texttospeech.SsmlVoiceGender:
        """
        Convert gender string to SSML gender enum.
        
        Args:
            gender: Gender preference string
            
        Returns:
            SSML gender enum value
        """
        gender_mapping = {
            "male": texttospeech.SsmlVoiceGender.MALE,
            "female": texttospeech.SsmlVoiceGender.FEMALE,
            "neutral": texttospeech.SsmlVoiceGender.NEUTRAL
        }
        
        return gender_mapping.get(gender.lower(), texttospeech.SsmlVoiceGender.NEUTRAL)
    
    def _extract_audio_duration(self, audio_data: bytes, text: str) -> float:
        """
        Extract audio duration from MP3 data or estimate from text.
        
        Args:
            audio_data: MP3 audio data
            text: Original text content
            
        Returns:
            Duration in seconds
        """
        # Reuse duration extraction logic (could be moved to a shared utility)
        try:
            duration = self._parse_mp3_duration(audio_data)
            if duration > 0:
                return duration
        except Exception as e:
            logger.debug(f"Could not parse MP3 duration: {e}")
        
        # Fallback to text-based estimation
        return self._estimate_duration(text)
    
    def _estimate_duration(self, text: str) -> float:
        """
        Estimate audio duration based on text length.
        
        Args:
            text: Text content
            
        Returns:
            Estimated duration in seconds
        """
        # Rough estimation: ~150 words per minute average speaking rate
        word_count = len(text.split())
        return (word_count / 150) * 60  # Convert to seconds
    
    def _validate_mp3_format(self, audio_data: bytes) -> bool:
        """
        Validate that audio data is in MP3 format.
        
        Args:
            audio_data: Raw audio data bytes
            
        Returns:
            True if valid MP3 format
        """
        if not audio_data or len(audio_data) < 4:
            return False
        
        # Check for MP3 header signatures
        # Check for ID3v2 tag (starts with "ID3")
        if audio_data[:3] == b'ID3':
            return True
        
        # Check for MP3 frame sync (11 bits set to 1)
        if len(audio_data) >= 2:
            if audio_data[0] == 0xFF and (audio_data[1] & 0xE0) == 0xE0:
                return True
        
        # Additional check for common MP3 patterns
        for i in range(min(10, len(audio_data) - 1)):
            if audio_data[i] == 0xFF and (audio_data[i + 1] & 0xE0) == 0xE0:
                return True
        
        logger.warning("Audio data does not appear to be valid MP3 format")
        return False
    
    def _parse_mp3_duration(self, audio_data: bytes) -> float:
        """
        Parse MP3 duration from audio data headers.
        
        Args:
            audio_data: MP3 audio data
            
        Returns:
            Duration in seconds, or 0 if cannot be determined
        """
        # Simplified MP3 duration parsing (same logic as Gemini engine)
        if not audio_data or len(audio_data) < 4:
            return 0.0
        
        try:
            file_size = len(audio_data)
            
            # Estimate based on typical bitrates for TTS (usually 64-128 kbps)
            # This is a rough estimation
            estimated_bitrate = 96000  # 96 kbps typical for TTS
            duration = (file_size * 8) / estimated_bitrate
            
            # Sanity check
            if 0.1 <= duration <= 3600:
                return duration
                
        except Exception as e:
            logger.debug(f"Error parsing MP3 duration: {e}")
        
        return 0.0
    
    def _create_style_description(self, style_context: StyleContext) -> str:
        """
        Create a description of the applied style for logging.
        
        Args:
            style_context: Style context used
            
        Returns:
            Human-readable style description
        """
        parts = [f"Tone: {style_context.tone}"]
        
        if style_context.pace != "normal":
            parts.append(f"Pace: {style_context.pace}")
        
        if style_context.emphasis_words:
            parts.append(f"Emphasis: {', '.join(style_context.emphasis_words[:3])}")
        
        if style_context.emotional_indicators:
            parts.append(f"Emotion: {', '.join(style_context.emotional_indicators[:2])}")
        
        parts.append(f"Type: {style_context.presentation_type.value}")
        
        return " | ".join(parts)
    
    def is_language_supported(self, language_code: str) -> bool:
        """
        Check if language is supported by Traditional TTS.
        
        Args:
            language_code: Language code to check
            
        Returns:
            True if language is supported
        """
        return self.config.is_language_supported(language_code)
    
    def get_available_voices(self, language_code: str) -> List[str]:
        """
        Get available voices for a language.
        
        Args:
            language_code: Language code
            
        Returns:
            List of available voice names
        """
        return self.config.get_voices_for_language(language_code)
    
    def create_ssml_enhanced_text(
        self,
        text: str,
        style_hints: Dict[str, Any]
    ) -> str:
        """
        Create SSML-enhanced text from style hints.
        
        Args:
            text: Original text
            style_hints: Dictionary of style hints
            
        Returns:
            SSML-enhanced text
        """
        # Convert style hints to StyleContext
        style_context = StyleContext(
            tone=style_hints.get("tone", "professional"),
            pace=style_hints.get("pace", "normal"),
            emphasis_words=style_hints.get("emphasis_words", []),
            emotional_indicators=style_hints.get("emotional_indicators", []),
            presentation_type=style_hints.get("presentation_type", "business")
        )
        
        return self._enhance_text_with_ssml(text, style_context)


def create_traditional_tts_engine(
    client: Optional[texttospeech.TextToSpeechClient] = None,
    config: Optional[TraditionalTTSConfig] = None
) -> TraditionalTTSEngine:
    """
    Factory function to create Traditional TTS engine.
    
    Args:
        client: Optional TTS client (creates default if None)
        config: Optional configuration (uses default if None)
        
    Returns:
        Configured TraditionalTTSEngine instance
    """
    if client is None:
        client = texttospeech.TextToSpeechClient()
    
    if config is None:
        config = TraditionalTTSConfig()
    
    return TraditionalTTSEngine(client, config)