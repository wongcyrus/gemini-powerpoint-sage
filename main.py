#!/usr/bin/env python3
"""
Gemini Powerpoint Sage

Enhances PowerPoint presentations by generating speaker notes using a
Supervisor-Tool Multi-Agent System.

This module serves as the entry point and CLI interface for the speaker
note generation system. The actual processing logic is delegated to
specialized service modules.
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import Config
# Note: Config is imported from config.py (root module), not config package
from services.presentation_processor import PresentationProcessor

# Setup logging with both file and console output
logs_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(logs_dir, exist_ok=True)

log_filename = f"gemini_powerpoint_sage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = os.path.join(logs_dir, log_filename)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# File handler with DEBUG level
file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Console handler with INFO level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)
logger.info(f"Debug log file: {log_filepath}")


async def process_presentation(
    pptx_path: str,
    pdf_path: str,
    course_id: str = None,
    skip_visuals: bool = False,
    generate_videos: bool = False,
    language: str = "en",
    style: str = None,
) -> str:
    """
    Process a presentation and generate speaker notes.

    Args:
        pptx_path: Path to the PowerPoint file
        pdf_path: Path to the PDF export
        course_id: Optional course ID for context
        skip_visuals: Whether to skip visual generation
        generate_videos: Whether to generate videos for slides
        language: Language locale code
        style: Optional style/theme for content generation

    Returns:
        Path to the enhanced presentation file
    """
    # Late import to allow environment variable configuration
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # Import agents
    from agents.supervisor import supervisor_agent
    from agents.analyst import analyst_agent
    from agents.overviewer import overviewer_agent
    from agents.designer import designer_agent
    from agents.writer import writer_agent
    from agents.auditor import auditor_agent
    from agents.translator import translator_agent
    from agents.image_translator import image_translator_agent
    from agents.video_generator import video_generator_agent

    # Create configuration
    config = Config(
        pptx_path=pptx_path,
        pdf_path=pdf_path,
        course_id=course_id,
        skip_visuals=skip_visuals,
        generate_videos=generate_videos,
        language=language,
        style=style,
    )

    # Validate configuration
    config.validate()

    # Create processor
    processor = PresentationProcessor(
        config=config,
        supervisor_agent=supervisor_agent,
        analyst_agent=analyst_agent,
        writer_agent=writer_agent,
        auditor_agent=auditor_agent,
        overviewer_agent=overviewer_agent,
        designer_agent=designer_agent,
        translator_agent=translator_agent,
        image_translator_agent=image_translator_agent,
        video_generator_agent=video_generator_agent,
    )

    # Process presentation
    output_path_notes, output_path_visuals = await processor.process()

    logger.info("\n" + "="*60)
    logger.info("Processing complete!")
    logger.info(f"1. Notes only: {output_path_notes}")
    if output_path_visuals:
        logger.info(f"2. With visuals: {output_path_visuals}")
    else:
        logger.info("2. With visuals: [SKIPPED - missing images]")
    logger.info("="*60)

    return output_path_notes, output_path_visuals


async def process_folder(
    folder_path: str,
    course_id: str = None,
    retry_errors: bool = False,
    region: str = "global",
    skip_visuals: bool = False,
    generate_videos: bool = False,
    languages: str = "en",
    style: str = None,
) -> None:
    """
    Process all PPTX files in a folder.

    Args:
        folder_path: Path to folder containing PPTX files
        course_id: Optional course ID for context
        retry_errors: Whether to retry slides with errors
        region: Google Cloud region
        skip_visuals: Whether to skip visual generation
        generate_videos: Whether to generate videos for slides
        languages: Comma-separated language locale codes
        style: Optional style/theme for content generation
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found: {folder_path}")
        sys.exit(1)

    # Parse languages - ensure English is first
    lang_list = [lang.strip() for lang in languages.split(",")]
    if "en" not in lang_list:
        lang_list.insert(0, "en")
    elif lang_list[0] != "en":
        lang_list.remove("en")
        lang_list.insert(0, "en")

    # Find all PPTX or PPTM files
    pptx_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith((".pptx", ".pptm")) and not file.startswith('~$'):
            pptx_files.append(os.path.join(folder_path, file))

    if not pptx_files:
        print(f"No PPTX/PPTM files found in folder: {folder_path}")
        return

    logger.info(f"Found {len(pptx_files)} PPTX/PPTM file(s) to process")
    logger.info(f"Languages to process: {', '.join(lang_list)}")

    # Process each PPTX file
    for idx, pptx_path in enumerate(pptx_files, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing file {idx}/{len(pptx_files)}: "
                    f"{os.path.basename(pptx_path)}")
        logger.info(f"{'='*60}")

        # Find corresponding PDF
        pptx_base = os.path.splitext(pptx_path)[0]
        pdf_path = pptx_base + ".pdf"

        if not os.path.exists(pdf_path):
            logger.warning(
                f"PDF not found for {os.path.basename(pptx_path)}, "
                f"skipping..."
            )
            continue

        # Set environment variables for this file
        if retry_errors:
            os.environ["SPEAKER_NOTE_RETRY_ERRORS"] = "true"
        else:
            os.environ.pop("SPEAKER_NOTE_RETRY_ERRORS", None)

        if region:
            os.environ["GOOGLE_CLOUD_LOCATION"] = region

        # Process each language, English first
        for lang in lang_list:
            logger.info(f"\n--- Processing language: {lang} ---")
            
            try:
                # Process this presentation
                await process_presentation(
                    pptx_path,
                    pdf_path,
                    course_id,
                    skip_visuals,
                    generate_videos,
                    lang,
                    style
                )
                logger.info(
                    f"Successfully processed {os.path.basename(pptx_path)} "
                    f"({lang})"
                )
            except Exception as e:
                logger.error(
                    f"Error processing {os.path.basename(pptx_path)} "
                    f"({lang}): {e}",
                    exc_info=True
                )
                # Continue with next language
                continue

    logger.info(f"\n{'='*60}")
    logger.info(f"Batch processing complete: "
                f"{len(pptx_files)} file(s) processed")
    logger.info(f"{'='*60}")


def main():
    """Main entry point for the Gemini Powerpoint Sage CLI."""
    parser = argparse.ArgumentParser(
        description="Generate Speaker Notes with Supervisor Agent",
        epilog="Use --config to load settings from a YAML/JSON file for easier management."
    )
    parser.add_argument(
        "--config",
        help="Path to YAML configuration file. "
             "Command-line arguments override config file settings. "
             "Example: --config config.yaml"
    )
    parser.add_argument("--pptx", required=False, help="Path to input PPTX or PPTM")
    parser.add_argument("--folder", required=False, help="Path to folder containing PPTX files to process")
    parser.add_argument("--pdf", required=False, help="Path to input PDF (optional if PDF with same name is in PPTX folder)")
    parser.add_argument(
        "--course-id", help="Optional: Course ID to fetch theme context"
    )
    parser.add_argument(
        "--progress-file", help="Override path for progress JSON file"
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
        "--refine",
        help="Refine an existing progress JSON file for TTS (removes markdown, simplifies text). "
             "Outputs to <filename>_refined.json by default."
    )

    args = parser.parse_args()
    
    # Load configuration from file if specified
    config_dict = {}
    if args.config:
        from config.config_loader import ConfigFileLoader
        
        try:
            config_dict = ConfigFileLoader.load_from_file(args.config)
            ConfigFileLoader.validate_config(config_dict)
            # Merge with command-line arguments (CLI takes precedence)
            config_dict = ConfigFileLoader.merge_with_args(config_dict, args)
            
            # Update args with config values
            for key, value in config_dict.items():
                if not hasattr(args, key) or getattr(args, key) is None:
                    setattr(args, key, value)
            
            logger.info(f"Loaded configuration from: {args.config}")
        except Exception as e:
            print(f"Error loading configuration file: {e}")
            sys.exit(1)
    
    # Handle refinement mode
    if args.refine:
        # Import RefinementProcessor
        from services.refinement_processor import RefinementProcessor
        from agents.refiner import refiner_agent
        
        input_path = os.path.abspath(args.refine)
        if not os.path.exists(input_path):
            print(f"Error: Path not found: {input_path}")
            sys.exit(1)

        processor = RefinementProcessor(refiner_agent)

        async def run_batch_refinement(files):
            for file_path, output_path in files:
                try:
                    logger.info(f"Refining: {os.path.basename(file_path)} -> {os.path.basename(output_path)}")
                    await processor.refine(file_path, output_path)
                except Exception as e:
                    logger.error(f"Failed to refine {file_path}: {e}")

        if os.path.isdir(input_path):
            # Process all JSON files in folder
            json_files = [
                f for f in os.listdir(input_path) 
                if f.lower().endswith('.json') and not f.lower().endswith('_refined.json')
            ]
            
            if not json_files:
                print(f"No suitable JSON files found in {input_path}")
                return

            logger.info(f"Found {len(json_files)} JSON files to refine in {input_path}")
            
            files_to_process = []
            for json_file in json_files:
                fp = os.path.join(input_path, json_file)
                base, ext = os.path.splitext(fp)
                op = f"{base}_refined{ext}"
                files_to_process.append((fp, op))
            
            asyncio.run(run_batch_refinement(files_to_process))
            
        else:
            # Single file mode
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_refined{ext}"
            
            logger.info(f"Refining JSON file: {input_path}")
            logger.info(f"Output will be saved to: {output_path}")
            
            asyncio.run(processor.refine(input_path, output_path))
            
        return
    
    # Validate that either --pptx or --folder is provided
    if not args.pptx and not args.folder:
        print("Error: Either --pptx or --folder must be provided.")
        parser.print_help()
        sys.exit(1)
    
    if args.pptx and args.folder:
        print("Error: Cannot use both --pptx and --folder at the same time.")
        sys.exit(1)
    
    # If folder mode, process all PPTX files in folder
    if args.folder:
        asyncio.run(process_folder(
            args.folder,
            args.course_id,
            args.retry_errors,
            args.region,
            args.skip_visuals,
            args.generate_videos,
            args.language,
            args.style
        ))
        return
    
    # Import utilities
    from utils.cli_utils import parse_languages, resolve_pptx_path, resolve_pdf_path
    
    # Parse languages
    lang_list = parse_languages(args.language)
    logger.info(f"Languages to process: {', '.join(lang_list)}")
    
    try:
        pptx_abs = resolve_pptx_path(args.pptx)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Resolve PDF path
    pdf_path = resolve_pdf_path(args.pdf, pptx_abs)
    
    if not pdf_path:
        # Prompt user for PDF path (must be inside pptx_dir)
        pptx_dir = os.path.dirname(pptx_abs)
        print("PDF file not found next to PPTX. Please input PDF filename (must be in same folder) or press Enter to abort:")
        while True:
            user_input = input("PDF filename (e.g. slides.pdf): ").strip()
            if not user_input:
                print("Aborting: PDF not provided.")
                return
            tentative = os.path.join(pptx_dir, user_input)
            if os.path.exists(tentative):
                pdf_path = tentative
                break
            else:
                print("File not found in PPTX folder. Try again or press Enter to abort.")

    # Final existence check
    if not pdf_path or not os.path.exists(pdf_path):
        print("Error: Valid PDF file not resolved. Exiting.")
        return

    # Resolve progress file path: default or relative names go next to PPTX
    # Note: Only set env var if user explicitly provided --progress-file
    # Otherwise, let progress_utils.py handle language-specific naming
    pptx_dir = os.path.dirname(pptx_abs)
    if args.progress_file:
        # If provided path is not absolute, place it in the PPTX directory
        if os.path.isabs(args.progress_file):
            progress_path = args.progress_file
        else:
            progress_path = os.path.join(pptx_dir, args.progress_file)
        os.environ["SPEAKER_NOTE_PROGRESS_FILE"] = progress_path
        logging.getLogger(__name__).info(
            f"Progress file resolved to: {progress_path}"
        )
    else:
        # Don't set env var - let progress_utils handle language suffix
        logging.getLogger(__name__).info(
            "Progress file will use language-specific naming: "
            f"{os.path.splitext(os.path.basename(pptx_abs))[0]}_"
            "{{language}}_progress.json"
        )
    if args.retry_errors:
        os.environ["SPEAKER_NOTE_RETRY_ERRORS"] = "true"

    # Set Google Cloud Location based on arg (override env if provided)
    if args.region:
        os.environ["GOOGLE_CLOUD_LOCATION"] = args.region
    elif "GOOGLE_CLOUD_LOCATION" not in os.environ:
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

    # Process each language, English first
    for lang in lang_list:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing language: {lang}")
        logger.info(f"{'='*60}")
        
        asyncio.run(
            process_presentation(
                pptx_abs, pdf_path, args.course_id, args.skip_visuals,
                args.generate_videos, lang, args.style
            )
        )


if __name__ == "__main__":
    main()
