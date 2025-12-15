#!/usr/bin/env python3

# Test script to verify TTS configuration
import sys
sys.path.insert(0, '.')

from config.tts_config import GeminiTTSConfig

def test_config():
    config = GeminiTTSConfig()
    print("=== Gemini TTS Configuration Test ===")
    print(f"Supported languages: {sorted(config.supported_languages)}")
    print(f"Total languages: {len(config.supported_languages)}")
    print(f"cmn-CN supported: {'cmn-CN' in config.supported_languages}")
    print(f"cmn-TW supported: {'cmn-TW' in config.supported_languages}")
    
    # Test the actual file content
    with open('config/tts_config.py', 'r') as f:
        content = f.read()
        print(f"File contains 'cmn-CN': {'cmn-CN' in content}")
        print(f"File contains 'cmn-TW': {'cmn-TW' in content}")

if __name__ == "__main__":
    test_config()