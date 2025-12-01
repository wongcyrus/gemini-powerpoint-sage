"""Refinement processing service."""

import logging
import os
from google.adk.agents import LlmAgent
from utils.progress_utils import load_progress, save_progress
from utils.agent_utils import run_stateless_agent

logger = logging.getLogger(__name__)


class RefinementProcessor:
    """Service for refining speaker notes."""

    def __init__(self, refiner_agent: LlmAgent):
        """
        Initialize the refinement processor.

        Args:
            refiner_agent: Agent for refining speaker notes
        """
        self.refiner_agent = refiner_agent

    async def refine(self, input_path: str, output_path: str):
        """
        Refine speaker notes in a progress JSON file.

        Args:
            input_path: Path to input JSON file
            output_path: Path to output JSON file
        """
        # Load
        data = load_progress(input_path)
        if not data or "slides" not in data:
            logger.error(f"Invalid progress file: {input_path}")
            return

        slides = data["slides"]
        total = len(slides)
        logger.info(f"Refining {total} slides from {input_path}...")

        count = 0
        for i, (key, slide_data) in enumerate(slides.items()):
            note = slide_data.get("note")
            slide_idx = slide_data.get("slide_index")
            
            if not note:
                continue

            logger.info(f"Refining slide {slide_idx} ({i+1}/{total})...")
            
            refined_note = await run_stateless_agent(
                self.refiner_agent,
                note
            )
            
            if refined_note:
                slide_data["note"] = refined_note
                slide_data["refined_from_original"] = True
                count += 1
            else:
                logger.warning(f"Refinement failed for slide {slide_idx}")

        # Save to output path
        save_progress(output_path, data)
        logger.info(f"Refined notes saved to {output_path} (Refined {count} slides)")
