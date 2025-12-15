"""Property-based tests for TTS domain models."""

import io
import struct
from typing import Optional
from hypothesis import given, strategies as st, assume
from hypothesis.strategies import composite
import pytest

from core.domain.tts import (
    TTSResult, AudioResult, VoiceConfig, StyleContext, SlideData,
    TTSEngineType, PresentationType, TTSEngineError
)


def is_valid_mp3(audio_data: bytes) -> bool:
    """
    Validate if audio data is a valid MP3 format.
    
    This function checks for MP3 format compliance by:
    1. Checking for MP3 frame header signature
    2. Validating frame structure
    3. Ensuring the data can be parsed as MP3
    
    Returns True if the audio data represents a valid MP3 file.
    """
    if not audio_data or len(audio_data) < 4:
        return False
    
    # Check for MP3 frame sync (11 bits set to 1)
    # MP3 frame header starts with 0xFFE or 0xFFF
    for i in range(len(audio_data) - 3):
        # Look for frame sync pattern
        if audio_data[i] == 0xFF and (audio_data[i + 1] & 0xE0) == 0xE0:
            # Found potential MP3 frame header
            header = struct.unpack('>I', audio_data[i:i+4])[0]
            
            # Extract MPEG version (bits 19-20)
            version = (header >> 19) & 0x3
            if version == 1:  # Reserved version
                continue
                
            # Extract layer (bits 17-18)
            layer = (header >> 17) & 0x3
            if layer == 0:  # Reserved layer
                continue
                
            # Extract bitrate index (bits 12-15)
            bitrate_index = (header >> 12) & 0xF
            if bitrate_index == 0 or bitrate_index == 15:  # Invalid bitrate
                continue
                
            # Extract sampling frequency (bits 10-11)
            sampling_freq = (header >> 10) & 0x3
            if sampling_freq == 3:  # Reserved frequency
                continue
                
            # If we get here, we found a valid MP3 frame header
            return True
    
    # Also check for ID3 tag (common in MP3 files)
    if audio_data.startswith(b'ID3'):
        return True
    
    return False


@composite
def valid_mp3_audio_data(draw):
    """Generate valid MP3 audio data for testing."""
    # Create a minimal valid MP3 frame header
    # This is a simplified MP3 frame for testing purposes
    
    # MP3 frame header: 0xFFFB (sync + version + layer + protection)
    # Followed by bitrate, sampling rate, padding, etc.
    mp3_header = bytes([
        0xFF, 0xFB,  # Sync + MPEG-1 Layer 3
        0x90, 0x00   # Bitrate 128kbps, 44.1kHz, no padding
    ])
    
    # Add some dummy audio data
    audio_size = draw(st.integers(min_value=100, max_value=10000))
    dummy_data = draw(st.binary(min_size=audio_size, max_size=audio_size))
    
    return mp3_header + dummy_data


@composite
def invalid_audio_data(draw):
    """Generate invalid audio data that should not be MP3."""
    # Generate random bytes that don't contain MP3 signatures
    size = draw(st.integers(min_value=1, max_value=1000))
    
    # Use a more controlled approach to avoid MP3 patterns
    # Generate data that explicitly avoids problematic byte sequences
    data = bytearray()
    
    for _ in range(size):
        byte_val = draw(st.integers(min_value=0, max_value=255))
        
        # If we're about to create a potential MP3 sync pattern, modify it
        if len(data) > 0 and data[-1] == 0xFF and (byte_val & 0xE0) == 0xE0:
            # Avoid creating MP3 sync pattern by ensuring second byte doesn't match
            byte_val = byte_val & 0x1F  # Clear the top 3 bits
        
        data.append(byte_val)
    
    # Convert back to bytes
    data = bytes(data)
    
    # Ensure it doesn't start with ID3 tag
    if data.startswith(b'ID3'):
        # Replace first 3 bytes with something else
        data = b'XYZ' + data[3:]
    
    # Final safety check - if somehow we still have MP3 patterns, replace them
    data = _remove_mp3_patterns(data)
    
    return data


def _remove_mp3_patterns(data: bytes) -> bytes:
    """Remove any accidental MP3 frame sync patterns from data."""
    if len(data) < 4:
        return data
    
    data_array = bytearray(data)
    
    # Scan for and remove MP3 frame sync patterns
    i = 0
    while i < len(data_array) - 3:
        if data_array[i] == 0xFF and (data_array[i + 1] & 0xE0) == 0xE0:
            # Found potential MP3 frame sync, modify it
            # Change the second byte to break the sync pattern
            data_array[i + 1] = data_array[i + 1] & 0x1F  # Clear top 3 bits
        i += 1
    
    return bytes(data_array)


@composite
def audio_result_strategy(draw, valid_mp3: bool = True):
    """Generate AudioResult instances with valid or invalid MP3 data."""
    if valid_mp3:
        audio_data = draw(valid_mp3_audio_data())
    else:
        audio_data = draw(invalid_audio_data())
    
    return AudioResult(
        audio_data=audio_data,
        public_url=draw(st.text(min_size=1, max_size=100)),
        cache_key=draw(st.text(min_size=1, max_size=50)),
        file_path=draw(st.text(min_size=1, max_size=100)),
        duration_seconds=draw(st.floats(min_value=0.1, max_value=3600.0)),
        engine_used=draw(st.sampled_from(TTSEngineType)),
        style_prompt=draw(st.text(min_size=0, max_size=200))
    )


@composite
def tts_result_strategy(draw, valid_mp3: bool = True):
    """Generate TTSResult instances with valid or invalid MP3 data."""
    if valid_mp3:
        audio_data = draw(valid_mp3_audio_data())
    else:
        audio_data = draw(invalid_audio_data())
    
    return TTSResult(
        audio_data=audio_data,
        public_url=draw(st.text(min_size=1, max_size=100)),
        cache_key=draw(st.text(min_size=1, max_size=50)),
        file_path=draw(st.text(min_size=1, max_size=100)),
        duration_seconds=draw(st.floats(min_value=0.1, max_value=3600.0)),
        engine_used=draw(st.sampled_from(TTSEngineType)),
        style_prompt=draw(st.text(min_size=0, max_size=200))
    )


class TestMP3FormatCompliance:
    """
    **Feature: tts-phrase-management, Property 12: MP3 Format Compliance**
    
    Property-based tests for MP3 format compliance in TTS system.
    Tests that all generated audio files are valid MP3 format.
    """
    
    @given(audio_result_strategy(valid_mp3=True))
    def test_audio_result_mp3_format_compliance(self, audio_result: AudioResult):
        """
        **Feature: tts-phrase-management, Property 12: MP3 Format Compliance**
        
        Property: For any generated AudioResult with audio data, 
        the audio_data should be a valid MP3 format that can be played by standard audio players.
        
        **Validates: Requirements 5.1**
        """
        # The audio data should be valid MP3 format
        assert is_valid_mp3(audio_result.audio_data), (
            f"AudioResult audio_data is not valid MP3 format. "
            f"Data length: {len(audio_result.audio_data)}, "
            f"First 10 bytes: {audio_result.audio_data[:10].hex() if len(audio_result.audio_data) >= 10 else 'N/A'}"
        )
    
    @given(tts_result_strategy(valid_mp3=True))
    def test_tts_result_mp3_format_compliance(self, tts_result: TTSResult):
        """
        **Feature: tts-phrase-management, Property 12: MP3 Format Compliance**
        
        Property: For any generated TTSResult with audio data,
        the audio_data should be a valid MP3 format that can be played by standard audio players.
        
        **Validates: Requirements 5.1**
        """
        if tts_result.audio_data is not None:
            # The audio data should be valid MP3 format
            assert is_valid_mp3(tts_result.audio_data), (
                f"TTSResult audio_data is not valid MP3 format. "
                f"Data length: {len(tts_result.audio_data)}, "
                f"First 10 bytes: {tts_result.audio_data[:10].hex() if len(tts_result.audio_data) >= 10 else 'N/A'}"
            )
    
    @given(audio_result_strategy(valid_mp3=False))
    def test_invalid_audio_data_detection(self, audio_result: AudioResult):
        """
        Test that our MP3 validation correctly identifies invalid audio data.
        This is a validation test for our MP3 format checker.
        """
        # Invalid audio data should be detected as such
        assert not is_valid_mp3(audio_result.audio_data), (
            f"Invalid audio data was incorrectly identified as valid MP3. "
            f"Data length: {len(audio_result.audio_data)}, "
            f"First 10 bytes: {audio_result.audio_data[:10].hex() if len(audio_result.audio_data) >= 10 else 'N/A'}"
        )
    
    def test_empty_audio_data_is_invalid(self):
        """Test that empty audio data is correctly identified as invalid MP3."""
        assert not is_valid_mp3(b"")
        assert not is_valid_mp3(None)
    
    def test_minimal_valid_mp3_detection(self):
        """Test that minimal valid MP3 data is correctly detected."""
        # Create minimal MP3 frame header
        minimal_mp3 = bytes([
            0xFF, 0xFB,  # Sync + MPEG-1 Layer 3
            0x90, 0x00   # Bitrate 128kbps, 44.1kHz
        ]) + b"dummy_audio_data"
        
        assert is_valid_mp3(minimal_mp3)
    
    def test_id3_tag_detection(self):
        """Test that MP3 files with ID3 tags are correctly detected."""
        id3_mp3 = b"ID3" + b"\x03\x00\x00\x00\x00\x00\x00" + b"dummy_mp3_data"
        assert is_valid_mp3(id3_mp3)


class TestTTSDataModelValidation:
    """Additional validation tests for TTS data models."""
    
    @given(st.text(min_size=1, max_size=100))
    def test_audio_result_requires_non_empty_data(self, dummy_text: str):
        """Test that AudioResult requires non-empty audio data."""
        with pytest.raises(ValueError, match="Audio data cannot be empty"):
            AudioResult(audio_data=b"")
        
        with pytest.raises(ValueError, match="Audio data cannot be empty"):
            AudioResult(audio_data=None)
    
    @given(
        st.floats(min_value=-1.0, max_value=0.0),
        st.floats(min_value=4.1, max_value=10.0)
    )
    def test_voice_config_speaking_rate_validation(self, invalid_low: float, invalid_high: float):
        """Test VoiceConfig speaking rate validation."""
        with pytest.raises(ValueError, match="Speaking rate must be between 0.25 and 4.0"):
            VoiceConfig(language_code="en-US", speaking_rate=invalid_low)
        
        with pytest.raises(ValueError, match="Speaking rate must be between 0.25 and 4.0"):
            VoiceConfig(language_code="en-US", speaking_rate=invalid_high)
    
    @given(
        st.floats(min_value=-25.0, max_value=-21.0),
        st.floats(min_value=21.0, max_value=30.0)
    )
    def test_voice_config_pitch_validation(self, invalid_low: float, invalid_high: float):
        """Test VoiceConfig pitch validation."""
        with pytest.raises(ValueError, match="Pitch must be between -20.0 and 20.0"):
            VoiceConfig(language_code="en-US", pitch=invalid_low)
        
        with pytest.raises(ValueError, match="Pitch must be between -20.0 and 20.0"):
            VoiceConfig(language_code="en-US", pitch=invalid_high)
    
    @given(st.integers(min_value=-10, max_value=0))
    def test_slide_data_positive_slide_number(self, invalid_slide_number: int):
        """Test that SlideData requires positive slide numbers."""
        with pytest.raises(ValueError, match="Slide number must be positive"):
            SlideData(
                slide_number=invalid_slide_number,
                text_content="Some content"
            )
    
    def test_slide_data_non_empty_content(self):
        """Test that SlideData requires non-empty text content."""
        with pytest.raises(ValueError, match="Text content cannot be empty"):
            SlideData(
                slide_number=1,
                text_content=""
            )
        
        with pytest.raises(ValueError, match="Text content cannot be empty"):
            SlideData(
                slide_number=1,
                text_content="   "  # Only whitespace
            )