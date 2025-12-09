"""CLI interface for Gemini PowerPoint Sage."""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from .commands import ProcessCommand, BatchCommand, RefineCommand
from utils.cli_utils import parse_languages, resolve_pptx_path, resolve_pdf_path

logger = logging.getLogger(__name__)


class CLI:
    """Command-line interface handler."""
    
    def __init__(self):
        """Initialize CLI."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description="Generate Speaker Notes with Supervisor Agent",
            epilog="Use --config to load settings from a YAML file for easier management."
        )
        
        # Configuration file
        parser.add_argument(
            "--config",
            help="Path to YAML configuration file. "
                 "Command-line arguments override config file settings. "
                 "Example: --config config.yaml"
        )
        
        # Input files
        parser.add_argument(
            "--pptx",
            required=False,
            help="Path to input PPTX or PPTM"
        )
        parser.add_argument(
            "--folder",
            required=False,
            help="Path to folder containing PPTX files to process"
        )
        parser.add_argument(
            "--pdf",
            required=False,
            help="Path to input PDF (optional if PDF with same name is in PPTX folder)"
        )
        
        # Processing options
        parser.add_argument(
            "--course-id",
            help="Optional: Course ID to fetch theme context"
        )
        parser.add_argument(
            "--progress-file",
            help="Override path for progress JSON file"
        )
        parser.add_argument(
            "--retry-errors",
            action="store_true",
            help="Retry slides previously marked as error"
        )
        parser.add_argument(
            "--region",
            help="Google Cloud Region (default: global)",
            default="global"
        )
        parser.add_argument(
            "--skip-visuals",
            action="store_true",
            help="Skip visual generation and only update speaker notes"
        )
        parser.add_argument(
            "--generate-videos",
            action="store_true",
            help="Generate promotional videos for each slide using Veo 3.1"
        )
        parser.add_argument(
            "--language",
            help="Language locale(s) for speaker notes. "
                 "Comma-separated for multiple languages. "
                 "English (en) is always processed first. "
                 "Examples: en, 'en,zh-CN', 'en,yue-HK,zh-CN'",
            default="en"
        )
        parser.add_argument(
            "--style",
            help="Style/theme for content generation. "
                 "Influences both speaker notes and slide visuals. "
                 "Examples: 'Gundam', 'Cyberpunk', 'Minimalist', 'Corporate', 'Professional' (default)",
            default=None
        )
        parser.add_argument(
            "--output-dir",
            help="Output directory for processed files. "
                 "If not specified, files are saved in the same directory as input. "
                 "Useful when processing with different styles to avoid overwriting.",
            default=None
        )
        
        # Refinement mode
        parser.add_argument(
            "--refine",
            help="Refine an existing progress JSON file for TTS (removes markdown, simplifies text). "
                 "Outputs to <filename>_refined.json by default."
        )
        
        return parser
    
    def _load_config_file(self, args: argparse.Namespace) -> None:
        """Load and merge configuration from file."""
        if not args.config:
            return
        
        from config.config_loader import ConfigFileLoader
        
        try:
            config_dict = ConfigFileLoader.load_from_file(args.config)
            ConfigFileLoader.validate_config(config_dict)
            config_dict = ConfigFileLoader.merge_with_args(config_dict, args)
            
            # Update args with config values
            for key, value in config_dict.items():
                if not hasattr(args, key) or getattr(args, key) is None:
                    setattr(args, key, value)
            
            logger.info(f"Loaded configuration from: {args.config}")
        except Exception as e:
            print(f"Error loading configuration file: {e}")
            sys.exit(1)
    
    def _setup_environment(self, args: argparse.Namespace) -> None:
        """Setup environment variables."""
        # Progress file
        if args.progress_file:
            pptx_dir = os.path.dirname(os.path.abspath(args.pptx)) if args.pptx else os.getcwd()
            if os.path.isabs(args.progress_file):
                progress_path = args.progress_file
            else:
                progress_path = os.path.join(pptx_dir, args.progress_file)
            os.environ["SPEAKER_NOTE_PROGRESS_FILE"] = progress_path
            logger.info(f"Progress file resolved to: {progress_path}")
        
        # Retry errors
        if args.retry_errors:
            os.environ["SPEAKER_NOTE_RETRY_ERRORS"] = "true"
        
        # Google Cloud region
        if args.region:
            os.environ["GOOGLE_CLOUD_LOCATION"] = args.region
        elif "GOOGLE_CLOUD_LOCATION" not in os.environ:
            os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    
    async def _handle_refine(self, args: argparse.Namespace) -> None:
        """Handle refinement mode."""
        cmd = RefineCommand(args.refine)
        await cmd.execute()
    
    async def _handle_batch(self, args: argparse.Namespace) -> None:
        """Handle batch processing mode."""
        cmd = BatchCommand(
            folder_path=args.folder,
            course_id=args.course_id,
            retry_errors=args.retry_errors,
            region=args.region,
            skip_visuals=args.skip_visuals,
            generate_videos=args.generate_videos,
            languages=args.language,
            style=args.style,
            output_dir=args.output_dir,
        )
        await cmd.execute()
    
    async def _handle_single(self, args: argparse.Namespace) -> None:
        """Handle single file processing mode."""
        # Parse languages
        lang_list = parse_languages(args.language)
        logger.info(f"Languages to process: {', '.join(lang_list)}")
        
        # Resolve paths
        try:
            pptx_abs = resolve_pptx_path(args.pptx)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        
        pdf_path = resolve_pdf_path(args.pdf, pptx_abs)
        
        if not pdf_path:
            # Prompt user for PDF path
            pptx_dir = os.path.dirname(pptx_abs)
            print("PDF file not found next to PPTX. Please input PDF filename (must be in same folder) or press Enter to abort:")
            while True:
                user_input = input("PDF filename (e.g. slides.pdf): ").strip()
                if not user_input:
                    print("Aborting: PDF not provided.")
                    sys.exit(1)
                tentative = os.path.join(pptx_dir, user_input)
                if os.path.exists(tentative):
                    pdf_path = tentative
                    break
                else:
                    print("File not found in PPTX folder. Try again or press Enter to abort.")
        
        if not pdf_path or not os.path.exists(pdf_path):
            print("Error: Valid PDF file not resolved. Exiting.")
            sys.exit(1)
        
        # Process each language
        for lang in lang_list:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing language: {lang}")
            logger.info(f"{'='*60}")
            
            cmd = ProcessCommand(
                pptx_path=pptx_abs,
                pdf_path=pdf_path,
                course_id=args.course_id,
                skip_visuals=args.skip_visuals,
                generate_videos=args.generate_videos,
                language=lang,
                style=args.style,
                output_dir=args.output_dir,
            )
            await cmd.execute()
    
    def run(self, argv: Optional[list] = None) -> int:
        """
        Run the CLI.
        
        Args:
            argv: Command-line arguments (defaults to sys.argv)
            
        Returns:
            Exit code
        """
        # Load environment variables
        load_dotenv()
        
        # Parse arguments
        args = self.parser.parse_args(argv)
        
        # Load config file if specified
        self._load_config_file(args)
        
        # Handle refinement mode
        if args.refine:
            asyncio.run(self._handle_refine(args))
            return 0
        
        # Validate input
        if not args.pptx and not args.folder:
            print("Error: Either --pptx or --folder must be provided.")
            self.parser.print_help()
            return 1
        
        if args.pptx and args.folder:
            print("Error: Cannot use both --pptx and --folder at the same time.")
            return 1
        
        # Setup environment
        self._setup_environment(args)
        
        # Handle batch or single mode
        try:
            if args.folder:
                asyncio.run(self._handle_batch(args))
            else:
                asyncio.run(self._handle_single(args))
            return 0
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return 1
