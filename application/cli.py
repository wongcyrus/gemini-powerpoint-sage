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
        parser.add_argument(
            "--tts-only",
            action="store_true",
            help="Generate only TTS audio files (skip notes and visuals generation)"
        )
        parser.add_argument(
            "--synthesize-video",
            action="store_true",
            help="Synthesize video from slide images and audio files"
        )
        parser.add_argument(
            "--slides-dir",
            help="Directory containing slide images (for video synthesis). If --audio-dir is not specified, this directory will also be used for audio files."
        )
        parser.add_argument(
            "--audio-dir",
            help="Directory containing audio files (for video synthesis). If not specified, uses --slides-dir."
        )
        parser.add_argument(
            "--video-output",
            help="Output path for synthesized video file"
        )
        parser.add_argument(
            "--video-config",
            help="Video synthesis configuration (JSON string or file path)"
        )
        parser.add_argument(
            "--video-cache-stats",
            action="store_true",
            help="Show video synthesis cache statistics"
        )
        parser.add_argument(
            "--video-clear-cache",
            type=int,
            metavar="DAYS",
            help="Clear video synthesis cache (optionally older than DAYS)"
        )
        # Single-file processing options (only used with --pptx)
        parser.add_argument(
            "--language",
            help="Language locale(s) for single-file processing. "
                 "Examples: en, 'en,ja-JP', 'en,yue-HK,zh-CN'",
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
    
    async def _handle_tts_only(self, args: argparse.Namespace) -> None:
        """Handle TTS-only processing mode."""
        from utils.tts_cli_utils import TTSCLIUtility
        import json
        
        if not args.pptx:
            print("Error: --tts-only requires --pptx argument with path to presentation progress JSON file")
            return
        
        # Check if the file is a JSON progress file
        if not args.pptx.endswith('.json'):
            print("Error: --tts-only requires a JSON progress file, not a PPTX file")
            print("First run the normal processing to generate speaker notes, then use --tts-only on the progress JSON file")
            return
        
        try:
            tts_cli = TTSCLIUtility()
            result = await tts_cli.generate_tts_for_presentation(
                args.pptx,
                args.language,
                args.output_dir
            )
            
            print("TTS Generation Results:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            logger.error(f"TTS-only processing failed: {e}")
            print(f"Error: {e}")

    async def _handle_video_synthesis(self, args: argparse.Namespace) -> None:
        """Handle video synthesis mode."""
        from services.video_synthesis.video_synthesis_service import VideoSynthesisService
        from services.video_synthesis.progress_tracker import ProgressReporter
        from core.domain.video_synthesis import VideoSynthesisRequest, VideoConfig
        from services.video_synthesis.video_config_manager import VideoConfigManager
        from pathlib import Path
        import json
        
        try:
            print("Starting video synthesis with direct FFmpeg implementation...")
            print("🚀 Using anti-hang direct FFmpeg commands for reliability")
            
            # Validate required arguments
            if not args.slides_dir:
                print("Error: --slides-dir is required for video synthesis")
                return
            
            if not args.video_output:
                print("Error: --video-output is required for video synthesis")
                return
            
            slides_dir = Path(args.slides_dir)
            # Use slides_dir for audio if audio_dir not specified (same directory)
            audio_dir = Path(args.audio_dir) if args.audio_dir else slides_dir
            output_path = Path(args.video_output)
            
            # Validate directories exist
            if not slides_dir.exists():
                print(f"Error: Slides directory not found: {slides_dir}")
                return
            
            if not audio_dir.exists():
                print(f"Error: Audio directory not found: {audio_dir}")
                return
            
            # Show which directories are being used
            if slides_dir == audio_dir:
                print(f"Using directory for both slides and audio: {slides_dir}")
            else:
                print(f"Using slides directory: {slides_dir}")
                print(f"Using audio directory: {audio_dir}")
            
            # Find slide images and audio files with natural sorting
            from utils.file_sorting import natural_sort_files, print_file_pairing_preview
            
            slide_images = natural_sort_files(
                list(slides_dir.glob("*.png")) + list(slides_dir.glob("*.jpg")) + list(slides_dir.glob("*.jpeg"))
            )
            audio_files = natural_sort_files(list(audio_dir.glob("*.mp3")))
            
            if not slide_images:
                print(f"Error: No slide images found in {slides_dir}")
                return
            
            if not audio_files:
                print(f"Error: No audio files found in {audio_dir}")
                return
            
            if len(slide_images) != len(audio_files):
                print(f"Error: Number of slide images ({len(slide_images)}) must match number of audio files ({len(audio_files)})")
                return
            
            print(f"Found {len(slide_images)} slide images and {len(audio_files)} audio files")
            
            # Show file pairing preview with verification
            print_file_pairing_preview(slide_images, audio_files)
            
            # Create video configuration
            config_manager = VideoConfigManager()
            
            if args.video_config:
                # Load custom configuration
                try:
                    if args.video_config.startswith('{'):
                        # JSON string
                        config_dict = json.loads(args.video_config)
                    else:
                        # File path
                        with open(args.video_config, 'r') as f:
                            config_dict = json.load(f)
                    
                    video_config = config_manager.create_config_from_dict(config_dict)
                    print(f"Using custom video configuration")
                except Exception as e:
                    print(f"Error loading video configuration: {e}")
                    print("Using default configuration")
                    video_config = config_manager.create_default_config()
            else:
                video_config = config_manager.create_default_config()
            
            # Display configuration summary
            config_summary = config_manager.get_config_summary(video_config)
            print("Video Configuration:")
            for key, value in config_summary.items():
                print(f"  {key}: {value}")
            
            # Create synthesis request
            request = VideoSynthesisRequest(
                slide_images=slide_images,
                audio_files=audio_files,
                output_path=output_path,
                config=video_config,
                presentation_id=output_path.stem
            )
            
            # Create progress reporter
            progress_reporter = ProgressReporter(show_detailed=True)
            
            # Initialize video synthesis service
            video_service = VideoSynthesisService()
            
            # Synthesize video
            result = video_service.synthesize_video(
                request,
                progress_callback=progress_reporter.on_progress_update
            )
            
            # Report results
            if result.success:
                print(f"\n✓ Video synthesis completed successfully!")
                print(f"  Output: {result.output_path}")
                print(f"  Duration: {result.duration_seconds:.2f} seconds")
                print(f"  File size: {result.get_file_size_mb():.2f} MB")
                print(f"  Processing time: {result.processing_time_seconds:.2f} seconds")
                print(f"  Slides processed: {result.slides_processed}")
            else:
                print(f"\n✗ Video synthesis failed!")
                print(f"  Error: {result.error_message}")
                print(f"  Processing time: {result.processing_time_seconds:.2f} seconds")
                print(f"  Slides processed: {result.slides_processed}")
            
        except Exception as e:
            logger.error(f"Video synthesis failed: {e}")
            print(f"Error: {e}")

    async def _handle_video_cache_stats(self, args: argparse.Namespace) -> None:
        """Handle video cache statistics display."""
        from services.video_synthesis.file_manager import VideoFileManager
        
        try:
            print("Video Synthesis Cache Statistics")
            print("=" * 40)
            
            # Create a temporary file manager to access cache stats
            file_manager = VideoFileManager(enable_cache=True)
            stats = file_manager.get_cache_stats()
            
            if not stats.get('cache_enabled', False):
                print("Cache is disabled")
                return
            
            print(f"Cache Directory: {stats.get('cache_dir', 'Unknown')}")
            print(f"Cached Segments: {stats.get('cached_segments', 0)}")
            print(f"Total Cache Size: {stats.get('total_cache_size_mb', 0):.2f} MB")
            print(f"Total Cache Size: {stats.get('total_cache_size_bytes', 0):,} bytes")
            
            if 'error' in stats:
                print(f"Error: {stats['error']}")
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            print(f"Error: {e}")

    async def _handle_video_clear_cache(self, args: argparse.Namespace) -> None:
        """Handle video cache clearing."""
        from services.video_synthesis.file_manager import VideoFileManager
        
        try:
            older_than_days = args.video_clear_cache if args.video_clear_cache > 0 else None
            
            if older_than_days:
                print(f"Clearing video cache (files older than {older_than_days} days)...")
            else:
                print("Clearing entire video cache...")
            
            # Create a temporary file manager to access cache clearing
            file_manager = VideoFileManager(enable_cache=True)
            stats = file_manager.clear_cache(older_than_days)
            
            if not stats.get('cache_enabled', False):
                print("Cache is disabled")
                return
            
            print(f"Files removed: {stats.get('files_removed', 0)}")
            print(f"Space freed: {stats.get('size_freed_bytes', 0) / (1024*1024):.2f} MB")
            
            if stats.get('errors'):
                print("Errors encountered:")
                for error in stats['errors']:
                    print(f"  - {error}")
            
            print("Cache clearing completed!")
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            print(f"Error: {e}")

    async def _handle_processing(self, args: argparse.Namespace) -> None:
        """Handle processing modes."""
        # Handle TTS-only mode first
        if args.tts_only:
            await self._handle_tts_only(args)
            return
        
        # Handle video synthesis mode
        if args.synthesize_video:
            await self._handle_video_synthesis(args)
            return
        
        # Handle video cache commands
        if args.video_cache_stats:
            await self._handle_video_cache_stats(args)
            return
        
        if args.video_clear_cache is not None:
            await self._handle_video_clear_cache(args)
            return
        
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
            bool(args.style_config),
            bool(args.synthesize_video),
            bool(args.video_cache_stats),
            bool(args.video_clear_cache is not None)
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
