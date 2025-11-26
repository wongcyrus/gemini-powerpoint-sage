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

from config import Config
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
    language: str = "en",
) -> str:
    """
    Process a presentation and generate speaker notes.

    Args:
        pptx_path: Path to the PowerPoint file
        pdf_path: Path to the PDF export
        course_id: Optional course ID for context
        skip_visuals: Whether to skip visual generation

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

    # Create configuration
    config = Config(
        pptx_path=pptx_path,
        pdf_path=pdf_path,
        course_id=course_id,
        skip_visuals=skip_visuals,
        language=language,
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


def get_english_notes(pptx_path: str) -> dict:
    """
    Load English speaker notes as baseline for translation.
    
    Args:
        pptx_path: Path to the PPTX file
        
    Returns:
        Dictionary mapping slide indices to English notes
    """
    from utils.progress_utils import get_progress_file_path, load_progress
    
    en_progress_file = get_progress_file_path(pptx_path, "en")
    if not os.path.exists(en_progress_file):
        return {}
    
    en_progress = load_progress(en_progress_file)
    en_notes = {}
    
    for slide_key, slide_data in en_progress.get("slides", {}).items():
        if slide_data.get("status") == "success":
            slide_idx = slide_data.get("slide_index")
            note = slide_data.get("note")
            if slide_idx and note:
                en_notes[slide_idx] = note
    
    return en_notes


async def process_folder(
    folder_path: str,
    course_id: str = None,
    retry_errors: bool = False,
    region: str = "global",
    skip_visuals: bool = False,
    languages: str = "en",
) -> None:
    """
    Process all PPTX files in a folder.

    Args:
        folder_path: Path to folder containing PPTX files
        course_id: Optional course ID for context
        retry_errors: Whether to retry slides with errors
        region: Google Cloud region
        skip_visuals: Whether to skip visual generation
        languages: Comma-separated language locale codes
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
                    lang
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
        description="Generate Speaker Notes with Supervisor Agent"
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
        "--language",
        help="Language locale(s) for speaker notes. "
             "Comma-separated for multiple languages. "
             "English (en) is always processed first. "
             "Examples: en, 'en,zh-CN', 'en,yue-HK,zh-CN'",
        default="en"
    )

    args = parser.parse_args()
    
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
            args.language  # Pass as comma-separated string
        ))
        return
    
    # Parse languages for single file mode
    lang_list = [lang.strip() for lang in args.language.split(",")]
    if "en" not in lang_list:
        lang_list.insert(0, "en")
    elif lang_list[0] != "en":
        lang_list.remove("en")
        lang_list.insert(0, "en")
    
    logger.info(f"Languages to process: {', '.join(lang_list)}")
    
    # Normalize PPTX path (trim whitespace, replace non-breaking spaces)
    original_pptx_arg = args.pptx
    normalized_pptx_arg = original_pptx_arg.strip().replace('\u00A0', ' ')
    if not os.path.exists(normalized_pptx_arg):
        # Attempt fuzzy match by collapsing multiple spaces
        pptx_dir_try = os.path.dirname(normalized_pptx_arg) or os.getcwd()
        base_try = os.path.basename(normalized_pptx_arg)
        collapsed_target = ' '.join(base_try.split())
        resolved = None
        try:
            for fname in os.listdir(pptx_dir_try):
                if ' '.join(fname.split()) == collapsed_target:
                    resolved = os.path.join(pptx_dir_try, fname)
                    break
        except Exception:
            pass
        if resolved and os.path.exists(resolved):
            normalized_pptx_arg = resolved
        else:
            print("Error: PPTX/PPTM file not found after normalization attempts.")
            print(f"Provided: {original_pptx_arg}")
            print("Hint: Remove trailing spaces or unusual characters before .pptx or .pptm")
            # List nearby candidates for user assistance
            try:
                print("Nearby PPTX/PPTM files in directory:")
                for f in os.listdir(pptx_dir_try):
                    if f.lower().endswith(('.pptx', '.pptm')):
                        print(f"  - {f}")
            except Exception:
                pass
            sys.exit(1)

    pptx_abs = os.path.abspath(normalized_pptx_arg)
    pptx_dir = os.path.dirname(pptx_abs)
    pptx_base = os.path.splitext(os.path.basename(pptx_abs))[0]

    # Resolve PDF path
    pdf_path = args.pdf
    if pdf_path:
        pdf_path = os.path.abspath(pdf_path)
        # Enforce same directory
        if os.path.dirname(pdf_path) != pptx_dir:
            print("Provided PDF must be in the same folder as the PPTX/PPTM.")
            pdf_path = None
    if not pdf_path:
        # Attempt auto-detect with same basename
        candidate = os.path.join(pptx_dir, pptx_base + ".pdf")
        if os.path.exists(candidate):
            pdf_path = candidate
        else:
            # Prompt user for PDF path (must be inside pptx_dir)
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
    pptx_dir = os.path.dirname(os.path.abspath(args.pptx))
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
            f"{os.path.splitext(os.path.basename(args.pptx))[0]}_"
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
                pptx_abs, pdf_path, args.course_id, args.skip_visuals, lang
            )
        )


if __name__ == "__main__":
    main()
