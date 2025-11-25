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

from config import Config
from services.presentation_processor import PresentationProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def process_presentation(
    pptx_path: str,
    pdf_path: str,
    course_id: str = None,
    skip_visuals: bool = False,
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

    # Create configuration
    config = Config(
        pptx_path=pptx_path,
        pdf_path=pdf_path,
        course_id=course_id,
        skip_visuals=skip_visuals,
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
    )

    # Process presentation
    output_path_notes, output_path_visuals = await processor.process()

    logger.info("\n" + "="*60)
    logger.info("Processing complete!")
    logger.info(f"1. Notes only: {output_path_notes}")
    logger.info(f"2. With visuals: {output_path_visuals}")
    logger.info("="*60)

    return output_path_notes, output_path_visuals


def main():
    """Main entry point for the Gemini Powerpoint Sage CLI."""
    parser = argparse.ArgumentParser(
        description="Generate Speaker Notes with Supervisor Agent"
    )
    parser.add_argument("--pptx", required=True, help="Path to input PPTX")
    parser.add_argument("--pdf", required=True, help="Path to input PDF")
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

    args = parser.parse_args()

    if not os.path.exists(args.pptx) or not os.path.exists(args.pdf):
        print("Error: Input files not found.")
        return

    # Set environment variables from arguments
    if args.progress_file:
        os.environ["SPEAKER_NOTE_PROGRESS_FILE"] = args.progress_file
    if args.retry_errors:
        os.environ["SPEAKER_NOTE_RETRY_ERRORS"] = "true"

    # Set Google Cloud Location based on arg (override env if provided)
    if args.region:
        os.environ["GOOGLE_CLOUD_LOCATION"] = args.region
    elif "GOOGLE_CLOUD_LOCATION" not in os.environ:
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

    asyncio.run(
        process_presentation(
            args.pptx, args.pdf, args.course_id, args.skip_visuals
        )
    )


if __name__ == "__main__":
    main()
