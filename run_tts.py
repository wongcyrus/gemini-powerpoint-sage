#!/usr/bin/env python3
"""
Simple script to run TTS generation on existing presentation progress files.

Usage:
    python run_tts.py presentation_progress.json --language en-US
    python run_tts.py --test  # Test TTS engines
    python run_tts.py --stats # Get TTS statistics
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Generate TTS audio for presentations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate TTS for a presentation
  python run_tts.py presentation_progress.json --language en-US
  
  # Test TTS engines
  python run_tts.py --test
  
  # Get TTS statistics
  python run_tts.py --stats
  
  # Clean up old cache files
  python run_tts.py --cleanup --max-age 7
        """
    )
    
    # Main argument - presentation file or action
    parser.add_argument(
        'presentation',
        nargs='?',
        help='Path to presentation progress JSON file'
    )
    
    # Language option
    parser.add_argument(
        '--language', '-l',
        default='en-US',
        help='Language code for TTS generation (default: en-US)'
    )
    
    # Output directory
    parser.add_argument(
        '--output-dir', '-o',
        help='Output directory for audio files'
    )
    
    # Action options
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test TTS engines with sample text'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show TTS system statistics'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up old cache files'
    )
    
    parser.add_argument(
        '--max-age',
        type=int,
        default=7,
        help='Maximum age of files to keep during cleanup (days)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.presentation, args.test, args.stats, args.cleanup]):
        parser.print_help()
        return 1
    
    if args.presentation and not Path(args.presentation).exists():
        print(f"Error: File not found: {args.presentation}")
        return 1
    
    # Run the appropriate action
    return asyncio.run(run_tts_action(args))

async def run_tts_action(args):
    """Run the specified TTS action."""
    try:
        from utils.tts_cli_utils import TTSCLIUtility
        
        tts_cli = TTSCLIUtility()
        
        if args.test:
            print("Testing TTS engines...")
            result = await tts_cli.test_tts_engines()
            print(json.dumps(result, indent=2))
            
        elif args.stats:
            print("Getting TTS statistics...")
            result = tts_cli.get_tts_stats()
            print(json.dumps(result, indent=2))
            
        elif args.cleanup:
            print(f"Cleaning up cache files older than {args.max_age} days...")
            result = await tts_cli.cleanup_cache(args.max_age)
            print(json.dumps(result, indent=2))
            
        elif args.presentation:
            print(f"Generating TTS for: {args.presentation}")
            print(f"Language: {args.language}")
            
            result = await tts_cli.generate_tts_for_presentation(
                args.presentation,
                args.language,
                args.output_dir
            )
            
            print("\nTTS Generation Results:")
            print(json.dumps(result, indent=2))
            
            # Summary
            successful = result.get('successful', 0)
            total = result.get('total_slides', 0)
            print(f"\nSummary: {successful}/{total} slides processed successfully")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())