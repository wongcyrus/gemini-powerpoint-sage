#!/usr/bin/env python3

# Debug script to understand the configuration issue
import sys
sys.path.insert(0, '.')

def debug_config():
    print("=== Debug Configuration ===")
    
    # Read the file directly
    with open('config/tts_config.py', 'r') as f:
        lines = f.readlines()
    
    print("Lines 18-25 from file:")
    for i, line in enumerate(lines[17:25], 18):
        print(f"{i:2d}: {line.rstrip()}")
    
    # Try to import and see what happens
    try:
        from config.tts_config import GeminiTTSConfig
        config = GeminiTTSConfig()
        
        # Check the actual default_factory function
        import inspect
        print(f"\nGeminiTTSConfig source file: {inspect.getfile(GeminiTTSConfig)}")
        
        # Get the field definition
        import dataclasses
        fields = dataclasses.fields(GeminiTTSConfig)
        for field in fields:
            if field.name == 'supported_languages':
                print(f"Field default_factory: {field.default_factory}")
                if field.default_factory:
                    result = field.default_factory()
                    print(f"Default factory result: {sorted(result)}")
                break
        
    except Exception as e:
        print(f"Error importing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_config()