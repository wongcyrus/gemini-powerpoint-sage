"""Gemini TTS engine implementation with natural language style prompts."""

import logging
from typing import Optional, List, Dict, Any
import asyncio
import json
import hashlib
import io
import struct

from google.cloud import texttospeech
from google.api_core import exceptions as gcp_exceptions

from core.domain.tts import (
    TTSEngineType, VoiceConfig, StyleContext, TTSResult, TTSEngineError
)
from config.tts_config import GeminiTTSConfig

logger = logging.getLogger(__name__)


class GeminiTTSEngine:
    """
    Gemini TTS engine with natural language style control.
    
    Supports advanced style prompts for contextual speech generation
    using Google's Gemini TTS API with natural language instructions.
    """
    
    def __init__(self, client: texttospeech.TextToSpeechClient, config: GeminiTTSConfig):
        """
        Initialize Gemini TTS engine.
        
        Args:
            client: Google Cloud Text-to-Speech client
            config: Gemini TTS configuration
        """
        self.client = client
        self.config = config
        
        # Voice mapping for different languages with gender classification
        self.VOICE_MAPPING = config.voice_mapping
        
        # Gender classification for voices (simplified heuristics)
        self.FEMALE_VOICES = {
            "Aoede", "Callirrhoe", "Kore", "Zephyr", "Leda", "Pulcherrima", 
            "Vindemiatrix", "Despina", "Erinome", "Laomedeia", "Gacrux", 
            "Sulafat", "Autonoe", "Achernar"
        }
    
    async def synthesize_speech(
        self,
        text: str,
        style_prompt: str,
        voice_config: VoiceConfig,
        language_code: str
    ) -> TTSResult:
        """
        Synthesize speech using Gemini TTS with style control.
        
        Args:
            text: Text content to synthesize
            style_prompt: Natural language style instruction
            voice_config: Voice configuration parameters
            language_code: Target language code
            
        Returns:
            AudioResult with generated audio data
            
        Raises:
            TTSEngineError: If synthesis fails
        """
        try:
            # Select appropriate model based on style complexity
            model = self._select_model(style_prompt)
            
            # Build the synthesis request
            request = self._build_synthesis_request(
                text, style_prompt, voice_config, language_code, model
            )
            
            logger.info(f"Synthesizing speech with Gemini TTS model {model} for language {language_code}")
            logger.debug(f"Text length: {len(text)} chars, Style prompt length: {len(style_prompt)} chars")
            logger.debug(f"Voice: {voice_config.voice_name}, Model: {model}")
            logger.debug(f"Style prompt: {style_prompt[:100]}...")
            
            # Log first 100 chars of text for debugging
            text_preview = text[:100] + "..." if len(text) > 100 else text
            logger.debug(f"Text preview: {text_preview}")
            
            # Call Gemini TTS API with retry logic
            response = await self._call_tts_api_with_retry(request)
            
            # Validate and process audio response
            if not response.audio_content:
                raise TTSEngineError("Empty audio content received from Gemini TTS", TTSEngineType.GEMINI)
            
            # Validate MP3 format
            if not self._validate_mp3_format(response.audio_content):
                raise TTSEngineError("Generated audio is not valid MP3 format", TTSEngineType.GEMINI)
            
            # Extract audio metadata
            duration = self._extract_audio_duration(response.audio_content, text)
            
            return TTSResult(
                audio_data=response.audio_content,
                duration_seconds=duration,
                engine_used=TTSEngineType.GEMINI,
                style_prompt=style_prompt
            )
            
        except Exception as e:
            logger.error(f"Gemini TTS synthesis failed for language {language_code}: {e}")
            raise TTSEngineError(f"Gemini TTS failed: {e}", TTSEngineType.GEMINI)
    
    def _build_synthesis_request(
        self,
        text: str,
        style_prompt: str,
        voice_config: VoiceConfig,
        language_code: str,
        model: str
    ) -> texttospeech.SynthesizeSpeechRequest:
        """
        Build Gemini TTS request with natural language prompts.
        
        Args:
            text: Text to synthesize
            style_prompt: Natural language style instruction
            voice_config: Voice configuration
            language_code: Target language
            model: Gemini TTS model to use
            
        Returns:
            Configured synthesis request
        """
        # Select appropriate voice for language and gender preference
        available_voices = self.VOICE_MAPPING.get(language_code, self.VOICE_MAPPING.get("en-US", []))
        selected_voice = self._select_voice(available_voices, voice_config.gender)
        
        logger.debug(f"Available voices for {language_code}: {available_voices}")
        logger.debug(f"Selected voice: {selected_voice}, Gender preference: {voice_config.gender}")
        
        # Build voice selection with model_name for Gemini TTS
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=selected_voice or voice_config.voice_name,
            model_name=model  # Gemini TTS requires model_name in voice selection
        )
        
        # Build audio configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=voice_config.speaking_rate,
            pitch=voice_config.pitch,
            volume_gain_db=voice_config.volume_gain_db
        )
        
        # For Gemini TTS, use prompt in SynthesisInput
        synthesis_input = texttospeech.SynthesisInput(
            text=text,
            prompt=style_prompt  # Gemini TTS uses prompt field for style instructions
        )
        
        # Check total size to ensure we're under the 4000 byte limit
        total_size = len(text.encode('utf-8')) + len(style_prompt.encode('utf-8'))
        if total_size > 3800:  # Leave some buffer
            logger.warning(f"Request size {total_size} bytes may exceed Gemini TTS limit")
        else:
            logger.debug(f"Request size: {total_size} bytes (within limits)")
        
        # Create the request
        request = texttospeech.SynthesizeSpeechRequest(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        return request
    
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
                
                logger.debug(f"Gemini TTS synthesis successful on attempt {attempt + 1}")
                return response
                
            except (gcp_exceptions.GoogleAPIError, asyncio.TimeoutError) as e:
                last_exception = e
                wait_time = 2 ** attempt  # Exponential backoff
                
                # Get more detailed error information
                error_details = str(e)
                if hasattr(e, 'message'):
                    error_details = e.message
                elif hasattr(e, 'details'):
                    error_details = e.details
                
                logger.warning(
                    f"Gemini TTS attempt {attempt + 1} failed: {error_details}. "
                    f"Exception type: {type(e).__name__}. "
                    f"Retrying in {wait_time} seconds..."
                )
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(wait_time)
        
        # All retries failed
        raise TTSEngineError(
            f"Gemini TTS failed after {self.config.max_retries} attempts: {last_exception}",
            TTSEngineType.GEMINI
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
    
    def _select_model(self, style_prompt: str = None) -> str:
        """
        Get the configured Gemini TTS model.
        
        Args:
            style_prompt: Natural language style instruction (unused, kept for compatibility)
            
        Returns:
            Configured model ID
        """
        # Always use the configured model (style_prompt no longer affects model selection)
        logger.debug(f"Using configured TTS model: {self.config.model_id}")
        return self.config.model_id
    
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
        
        if preferred_gender.lower() == "female":
            female_available = [v for v in available_voices if v in self.FEMALE_VOICES]
            if female_available:
                return female_available[0]
        elif preferred_gender.lower() == "male":
            male_available = [v for v in available_voices if v not in self.FEMALE_VOICES]
            if male_available:
                return male_available[0]
        
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
    
    def is_language_supported(self, language_code: str) -> bool:
        """
        Check if language is supported by Gemini TTS.
        
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
    
    def create_style_enhanced_request(
        self,
        text: str,
        style_context: StyleContext,
        voice_config: VoiceConfig,
        language_code: str
    ) -> Dict[str, Any]:
        """
        Create enhanced request with style context for future Gemini TTS API.
        
        This method demonstrates how style context would be integrated
        into the actual Gemini TTS API when it becomes available.
        
        Args:
            text: Text to synthesize
            style_context: Style context information
            voice_config: Voice configuration
            language_code: Target language
            
        Returns:
            Enhanced request dictionary
        """
        # Select model and voice
        style_prompt = self._generate_style_prompt_from_context(style_context)
        model = self._select_model(style_prompt)
        available_voices = self.get_available_voices(language_code)
        selected_voice = self._select_voice(available_voices, voice_config.gender)
        
        # Build enhanced request structure
        enhanced_request = {
            "model": model,
            "text": text,
            "language_code": language_code,
            "voice": {
                "name": selected_voice,
                "gender": voice_config.gender,
                "speaking_rate": voice_config.speaking_rate,
                "pitch": voice_config.pitch,
                "volume_gain_db": voice_config.volume_gain_db
            },
            "style": {
                "prompt": style_prompt,
                "tone": style_context.tone,
                "pace": style_context.pace,
                "emphasis_words": style_context.emphasis_words,
                "emotional_indicators": style_context.emotional_indicators,
                "presentation_type": style_context.presentation_type.value,
                "confidence_score": style_context.confidence_score
            },
            "audio_config": {
                "encoding": "MP3",
                "sample_rate": 24000
            }
        }
        
        return enhanced_request
    
    def _generate_style_prompt_from_context(self, style_context: StyleContext) -> str:
        """
        Generate style prompt from style context.
        
        Args:
            style_context: Style context information
            
        Returns:
            Generated style prompt
        """
        prompt_parts = []
        
        # Base tone instruction
        tone_instructions = {
            "professional": "Speak in a professional, clear, and authoritative manner",
            "casual": "Use a friendly, conversational tone as if speaking to colleagues",
            "enthusiastic": "Deliver with energy and passion, showing excitement about the topic",
            "technical": "Speak precisely and methodically, emphasizing accuracy and clarity",
            "narrative": "Use a storytelling approach with natural flow and engaging rhythm"
        }
        
        base_instruction = tone_instructions.get(
            style_context.tone, 
            "Speak in a clear, professional manner"
        )
        prompt_parts.append(base_instruction)
        
        # Pace instruction
        if style_context.pace == "slow":
            prompt_parts.append("Speak slowly and deliberately, allowing time for comprehension")
        elif style_context.pace == "fast":
            prompt_parts.append("Maintain a brisk but clear pace")
        
        # Emphasis words
        if style_context.emphasis_words:
            emphasis_list = ", ".join(style_context.emphasis_words[:3])  # Limit to 3 words
            prompt_parts.append(f"Give special emphasis to these key concepts: {emphasis_list}")
        
        # Emotional indicators
        if style_context.emotional_indicators:
            emotion = style_context.emotional_indicators[0]  # Use first emotion
            prompt_parts.append(f"Convey {emotion} emotion in your delivery")
        
        # Presentation type context
        type_context = {
            "business": "This is a business presentation, so maintain professionalism and engagement",
            "academic": "This is academic content, so emphasize precision and scholarly tone",
            "training": "This is training material, so focus on clear instruction and learning",
            "technical": "This is technical documentation, so emphasize accuracy and detail",
            "narrative": "This is storytelling content, so use natural narrative flow"
        }
        
        context_instruction = type_context.get(style_context.presentation_type.value)
        if context_instruction:
            prompt_parts.append(context_instruction)
        
        return ". ".join(prompt_parts) + "."
    
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
        # MP3 files can start with ID3 tag or directly with MP3 frame
        
        # Check for ID3v2 tag (starts with "ID3")
        if audio_data[:3] == b'ID3':
            return True
        
        # Check for MP3 frame sync (11 bits set to 1)
        # MP3 frame header starts with 0xFF followed by 0xE0-0xFF
        if len(audio_data) >= 2:
            if audio_data[0] == 0xFF and (audio_data[1] & 0xE0) == 0xE0:
                return True
        
        # Additional check for common MP3 patterns
        # Look for frame sync pattern in first few bytes
        for i in range(min(10, len(audio_data) - 1)):
            if audio_data[i] == 0xFF and (audio_data[i + 1] & 0xE0) == 0xE0:
                return True
        
        logger.warning("Audio data does not appear to be valid MP3 format")
        return False
    
    def _extract_audio_duration(self, audio_data: bytes, text: str) -> float:
        """
        Extract audio duration from MP3 data or estimate from text.
        
        Args:
            audio_data: MP3 audio data
            text: Original text content
            
        Returns:
            Duration in seconds
        """
        try:
            # Try to extract duration from MP3 headers
            duration = self._parse_mp3_duration(audio_data)
            if duration > 0:
                return duration
        except Exception as e:
            logger.debug(f"Could not parse MP3 duration: {e}")
        
        # Fallback to text-based estimation
        return self._estimate_duration(text)
    
    def _parse_mp3_duration(self, audio_data: bytes) -> float:
        """
        Parse MP3 duration from audio data headers.
        
        Args:
            audio_data: MP3 audio data
            
        Returns:
            Duration in seconds, or 0 if cannot be determined
        """
        if not audio_data or len(audio_data) < 4:
            return 0.0
        
        try:
            # Simple MP3 duration estimation based on file size and bitrate
            # This is a simplified approach - full MP3 parsing would be more complex
            
            file_size = len(audio_data)
            
            # Look for first MP3 frame to determine bitrate
            frame_start = self._find_mp3_frame_start(audio_data)
            if frame_start == -1:
                return 0.0
            
            # Parse MP3 frame header to get bitrate and sample rate
            if frame_start + 4 > len(audio_data):
                return 0.0
            
            header = struct.unpack('>I', audio_data[frame_start:frame_start + 4])[0]
            
            # Extract bitrate and sample rate from header
            bitrate_index = (header >> 12) & 0xF
            sample_rate_index = (header >> 10) & 0x3
            
            # MP3 bitrate table (simplified for MPEG-1 Layer III)
            bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
            sample_rates = [44100, 48000, 32000, 0]
            
            if bitrate_index >= len(bitrates) or sample_rate_index >= len(sample_rates):
                return 0.0
            
            bitrate = bitrates[bitrate_index] * 1000  # Convert to bps
            sample_rate = sample_rates[sample_rate_index]
            
            if bitrate == 0 or sample_rate == 0:
                return 0.0
            
            # Calculate duration: (file_size * 8) / bitrate
            duration = (file_size * 8) / bitrate
            
            # Sanity check - duration should be reasonable
            if 0.1 <= duration <= 3600:  # Between 0.1 seconds and 1 hour
                return duration
            
        except Exception as e:
            logger.debug(f"Error parsing MP3 duration: {e}")
        
        return 0.0
    
    def _find_mp3_frame_start(self, audio_data: bytes) -> int:
        """
        Find the start of the first MP3 frame.
        
        Args:
            audio_data: MP3 audio data
            
        Returns:
            Byte offset of first MP3 frame, or -1 if not found
        """
        # Skip ID3v2 tag if present
        offset = 0
        if len(audio_data) >= 10 and audio_data[:3] == b'ID3':
            # ID3v2 tag size is in bytes 6-9 (synchsafe integer)
            size = (audio_data[6] << 21) | (audio_data[7] << 14) | (audio_data[8] << 7) | audio_data[9]
            offset = 10 + size
        
        # Look for MP3 frame sync
        for i in range(offset, min(offset + 1000, len(audio_data) - 1)):
            if audio_data[i] == 0xFF and (audio_data[i + 1] & 0xE0) == 0xE0:
                return i
        
        return -1
    
    def validate_audio_quality(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Validate audio quality and extract metadata.
        
        Args:
            audio_data: MP3 audio data
            
        Returns:
            Dictionary with quality metrics and metadata
        """
        quality_info = {
            "is_valid_mp3": False,
            "file_size_bytes": len(audio_data),
            "estimated_bitrate": 0,
            "has_id3_tag": False,
            "quality_score": 0.0
        }
        
        if not audio_data:
            return quality_info
        
        # Check MP3 format
        quality_info["is_valid_mp3"] = self._validate_mp3_format(audio_data)
        
        # Check for ID3 tag
        quality_info["has_id3_tag"] = len(audio_data) >= 3 and audio_data[:3] == b'ID3'
        
        # Estimate bitrate
        frame_start = self._find_mp3_frame_start(audio_data)
        if frame_start != -1 and frame_start + 4 <= len(audio_data):
            try:
                header = struct.unpack('>I', audio_data[frame_start:frame_start + 4])[0]
                bitrate_index = (header >> 12) & 0xF
                bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
                if bitrate_index < len(bitrates):
                    quality_info["estimated_bitrate"] = bitrates[bitrate_index]
            except Exception:
                pass
        
        # Calculate quality score
        score = 0.0
        if quality_info["is_valid_mp3"]:
            score += 0.4
        if quality_info["file_size_bytes"] > 1000:  # Reasonable file size
            score += 0.2
        if quality_info["estimated_bitrate"] >= 128:  # Good bitrate
            score += 0.3
        if quality_info["has_id3_tag"]:
            score += 0.1
        
        quality_info["quality_score"] = score
        
        return quality_info


def create_gemini_tts_engine(
    client: Optional[texttospeech.TextToSpeechClient] = None,
    config: Optional[GeminiTTSConfig] = None
) -> GeminiTTSEngine:
    """
    Factory function to create Gemini TTS engine.
    
    Args:
        client: Optional TTS client (creates default if None)
        config: Optional configuration (uses default if None)
        
    Returns:
        Configured GeminiTTSEngine instance
    """
    if client is None:
        client = texttospeech.TextToSpeechClient()
    
    if config is None:
        config = GeminiTTSConfig()
    
    return GeminiTTSEngine(client, config)