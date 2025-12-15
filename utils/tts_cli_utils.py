"""TTS CLI utilities for command-line operations."""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from config.tts_config import get_tts_config
from core.domain.tts import SlideData
from services.tts.tts_orchestrator import create_tts_orchestrator

logger = logging.getLogger(__name__)


class TTSCLIUtility:
    """Command-line utility for TTS operations."""
    
    def __init__(self):
        """Initialize TTS CLI utility."""
        self.tts_config = get_tts_config()
        self.orchestrator = None
    
    async def initialize(self):
        """Initialize TTS orchestrator."""
        if not self.tts_config.enabled:
            raise RuntimeError("TTS system is disabled in configuration")
        
        try:
            self.orchestrator = create_tts_orchestrator(self.tts_config)
            logger.info("TTS orchestrator initialized successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize TTS orchestrator: {e}")
    
    async def generate_tts_for_presentation(
        self,
        presentation_path: str,
        language: str = "en-US",
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        Generate TTS for an existing presentation progress file.
        
        Args:
            presentation_path: Path to presentation progress JSON file
            language: Language code for TTS generation
            output_dir: Optional output directory override
            
        Returns:
            Dictionary with generation results
        """
        if not self.orchestrator:
            await self.initialize()
        
        # Load presentation progress
        if not os.path.exists(presentation_path):
            raise FileNotFoundError(f"Presentation file not found: {presentation_path}")
        
        with open(presentation_path, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
        
        # Extract slide data
        slides_data = []
        presentation_id = Path(presentation_path).stem
        
        for slide_key, slide_info in progress_data.get("slides", {}).items():
            if slide_info.get("status") == "success" and slide_info.get("note"):
                slide_data = SlideData(
                    slide_number=slide_info["slide_index"],
                    text_content=slide_info["note"],
                    speaker_notes=slide_info["note"],
                    language_code=language,
                    presentation_id=presentation_id
                )
                slides_data.append(slide_data)
        
        if not slides_data:
            raise ValueError("No valid slides found in presentation progress file")
        
        logger.info(f"Generating TTS for {len(slides_data)} slides in {language}")
        
        # Generate TTS
        results = await self.orchestrator.process_single_language_batch(
            slides_data, language, presentation_id
        )
        
        # Compile results
        successful = sum(1 for result in results if result.is_valid())
        failed = len(results) - successful
        
        result_summary = {
            "presentation_id": presentation_id,
            "language": language,
            "total_slides": len(slides_data),
            "successful": successful,
            "failed": failed,
            "results": []
        }
        
        for i, result in enumerate(results):
            slide_result = {
                "slide_number": slides_data[i].slide_number,
                "success": result.is_valid(),
                "file_path": result.file_path if result.is_valid() else None,
                "duration_seconds": result.duration_seconds,
                "engine_used": result.engine_used.value,
                "error": result.metadata.get("error") if not result.is_valid() else None
            }
            result_summary["results"].append(slide_result)
        
        logger.info(f"TTS generation completed: {successful}/{len(slides_data)} successful")
        return result_summary
    
    async def test_tts_engines(self) -> Dict[str, Any]:
        """
        Test TTS engines with sample text.
        
        Returns:
            Dictionary with test results
        """
        if not self.orchestrator:
            await self.initialize()
        
        test_text = "This is a test of the text-to-speech system."
        test_languages = ["en-US", "ja-JP", "yue-HK"]
        
        results = {
            "test_text": test_text,
            "languages": {}
        }
        
        for language in test_languages:
            logger.info(f"Testing TTS for language: {language}")
            
            try:
                result = await self.orchestrator.generate_speech_for_slide(
                    slide_number=1,
                    text_content=test_text,
                    speaker_notes="Test speaker notes for TTS validation.",
                    language_code=language,
                    presentation_id="tts_test"
                )
                
                results["languages"][language] = {
                    "success": result.is_valid(),
                    "engine_used": result.engine_used.value,
                    "duration_seconds": result.duration_seconds,
                    "file_size_bytes": len(result.audio_data) if result.audio_data else 0,
                    "error": result.metadata.get("error") if not result.is_valid() else None
                }
                
            except Exception as e:
                results["languages"][language] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def cleanup_cache(self, max_age_days: int = 7) -> Dict[str, Any]:
        """
        Clean up TTS cache files.
        
        Args:
            max_age_days: Maximum age of files to keep
            
        Returns:
            Dictionary with cleanup results
        """
        if not self.orchestrator:
            await self.initialize()
        
        # Clean up cache
        cache_cleaned = await self.orchestrator.cache_manager.cleanup_expired_entries()
        
        # Clean up storage
        storage_cleaned = self.orchestrator.storage_manager.cleanup_old_files(max_age_days)
        
        return {
            "cache_entries_cleaned": cache_cleaned,
            "storage_files_cleaned": storage_cleaned,
            "max_age_days": max_age_days
        }
    
    def get_tts_stats(self) -> Dict[str, Any]:
        """
        Get TTS system statistics.
        
        Returns:
            Dictionary with TTS statistics
        """
        if not self.orchestrator:
            return {"error": "TTS orchestrator not initialized"}
        
        return self.orchestrator.get_orchestrator_stats()


def create_tts_cli_parser() -> argparse.ArgumentParser:
    """Create TTS CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="TTS CLI Utility for Gemini PowerPoint Sage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate TTS for a presentation
  python -m utils.tts_cli_utils generate presentation.json --language en-US
  
  # Test TTS engines
  python -m utils.tts_cli_utils test
  
  # Clean up cache
  python -m utils.tts_cli_utils cleanup --max-age 7
  
  # Get TTS statistics
  python -m utils.tts_cli_utils stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate TTS for presentation')
    generate_parser.add_argument('presentation', help='Path to presentation progress JSON file')
    generate_parser.add_argument('--language', '-l', default='en-US', 
                                help='Language code (default: en-US)')
    generate_parser.add_argument('--output-dir', '-o', 
                                help='Output directory override')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test TTS engines')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up TTS cache')
    cleanup_parser.add_argument('--max-age', type=int, default=7,
                               help='Maximum age of files to keep in days (default: 7)')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Get TTS system statistics')
    
    return parser


async def main():
    """Main CLI entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = create_tts_cli_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        tts_cli = TTSCLIUtility()
        
        if args.command == 'generate':
            result = await tts_cli.generate_tts_for_presentation(
                args.presentation,
                args.language,
                args.output_dir
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == 'test':
            result = await tts_cli.test_tts_engines()
            print(json.dumps(result, indent=2))
            
        elif args.command == 'cleanup':
            result = await tts_cli.cleanup_cache(args.max_age)
            print(json.dumps(result, indent=2))
            
        elif args.command == 'stats':
            result = tts_cli.get_tts_stats()
            print(json.dumps(result, indent=2))
        
        return 0
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))