"""CLI interface for Gemini PowerPoint Sage."""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from .unified_processor import UnifiedProcessor
from .commands import RefineCommand
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
            epilog="Configuration is handled through YAML files in styles/ directory. "
                   "Use --styles for all styles, --style-config for one specific style."
        )
        
        # Configuration file
        parser.add_argument(
            "--config",
            help="Path to YAML configuration file. "
                 "Command-line arguments override config file settings. "
                 "Example: --config config.yaml"
        )
        
        # Input modes
        parser.add_argument(
            "--pptx",
            required=False,
            help="Path to input PPTX or PPTM file (for single file processing)"
        )
        parser.add_argument(
            "--pdf",
            required=False,
            help="Path to input PDF (optional if PDF with same name is in PPTX folder)"
        )
        parser.add_argument(
            "--styles",
            action="store_true",
            help="Process using YAML configurations in styles/ directory (recommended)"
        )
        parser.add_argument(
            "--style-config",
            help="Process using a specific YAML style configuration file. "
                 "Examples: 'cyberpunk', 'professional', 'gundam' or full path to config file"
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
        # Single-file processing options (only used with --pptx)
        parser.add_argument(
            "--language",
            help="Language locale(s) for single-file processing. "
                 "Examples: en, 'en,zh-CN', 'en,yue-HK,zh-CN'",
            default="en"
        )
        parser.add_argument(
            "--style",
            help="Style/theme for single-file processing. "
                 "Examples: 'gundam', 'cyberpunk', 'professional'",
            default="professional"
        )
        parser.add_argument(
            "--output-dir",
            help="Output directory for single-file processing.",
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
    
    async def _handle_processing(self, args: argparse.Namespace) -> None:
        """Handle processing modes."""
        # Determine processing mode
        if args.pptx:
            # Single file mode - use CLI parameters
            logger.info("Processing single file...")
            processor = UnifiedProcessor(
                root_path=".",
                course_id=args.course_id,
                skip_visuals=args.skip_visuals,
                generate_videos=args.generate_videos,
                retry_errors=args.retry_errors,
                region=args.region
            )
            await processor.process_single_file(
                args.pptx, 
                args.pdf,
                language=args.language,
                style=args.style,
                output_dir=args.output_dir
            )
            
        elif args.styles:
            # YAML-driven styles processing (all styles)
            logger.info("Processing with YAML configurations...")
            processor = UnifiedProcessor(
                root_path=".",
                course_id=args.course_id,
                skip_visuals=args.skip_visuals,
                generate_videos=args.generate_videos,
                retry_errors=args.retry_errors,
                region=args.region
            )
            await processor.process_styles_directory()
            
        elif args.style_config:
            # Single style configuration processing
            logger.info(f"Processing with single style configuration: {args.style_config}")
            processor = UnifiedProcessor(
                root_path=".",
                course_id=args.course_id,
                skip_visuals=args.skip_visuals,
                generate_videos=args.generate_videos,
                retry_errors=args.retry_errors,
                region=args.region
            )
            await processor.process_single_style(args.style_config)
        
        else:
            # Default to styles processing
            logger.info("No mode specified, defaulting to YAML-driven styles processing...")
            processor = UnifiedProcessor(
                root_path=".",
                course_id=args.course_id,
                skip_visuals=args.skip_visuals,
                generate_videos=args.generate_videos,
                retry_errors=args.retry_errors,
                region=args.region
            )
            await processor.process_styles_directory()
    
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
        
        # Validate input methods
        input_methods = sum([
            bool(args.pptx),
            bool(args.styles),
            bool(args.style_config)
        ])
        
        if input_methods > 1:
            print("Error: Cannot use multiple input methods at the same time.")
            return 1
        
        # Setup environment
        self._setup_environment(args)
        
        # Handle processing
        try:
            asyncio.run(self._handle_processing(args))
            return 0
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return 1
