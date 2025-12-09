"""Refine command for TTS optimization."""

import logging
import os
from typing import List, Tuple

from .base import Command
from services.refinement_processor import RefinementProcessor
from agents.refiner import refiner_agent

logger = logging.getLogger(__name__)


class RefineCommand(Command):
    """Command to refine speaker notes for TTS."""
    
    def __init__(self, input_path: str):
        """
        Initialize refine command.
        
        Args:
            input_path: Path to JSON file or folder containing JSON files
        """
        self.input_path = os.path.abspath(input_path)
        self.processor = RefinementProcessor(refiner_agent)
    
    def validate(self) -> None:
        """Validate command parameters."""
        if not os.path.exists(self.input_path):
            raise ValueError(f"Path not found: {self.input_path}")
    
    def _find_json_files(self) -> List[Tuple[str, str]]:
        """
        Find JSON files to process.
        
        Returns:
            List of (input_path, output_path) tuples
        """
        files = []
        
        if os.path.isdir(self.input_path):
            # Process all JSON files in folder
            json_files = [
                f for f in os.listdir(self.input_path)
                if f.lower().endswith('.json') and not f.lower().endswith('_refined.json')
            ]
            
            for json_file in json_files:
                fp = os.path.join(self.input_path, json_file)
                base, ext = os.path.splitext(fp)
                op = f"{base}_refined{ext}"
                files.append((fp, op))
        else:
            # Single file mode
            base, ext = os.path.splitext(self.input_path)
            output_path = f"{base}_refined{ext}"
            files.append((self.input_path, output_path))
        
        return files
    
    async def execute(self) -> None:
        """Execute refinement."""
        self.validate()
        
        files = self._find_json_files()
        
        if not files:
            logger.warning(f"No suitable JSON files found in {self.input_path}")
            return
        
        if len(files) == 1:
            logger.info(f"Refining JSON file: {files[0][0]}")
            logger.info(f"Output will be saved to: {files[0][1]}")
        else:
            logger.info(f"Found {len(files)} JSON files to refine in {self.input_path}")
        
        # Process each file
        for file_path, output_path in files:
            try:
                logger.info(
                    f"Refining: {os.path.basename(file_path)} -> "
                    f"{os.path.basename(output_path)}"
                )
                await self.processor.refine(file_path, output_path)
                logger.info(f"✓ Successfully refined: {os.path.basename(file_path)}")
            except Exception as e:
                logger.error(f"Failed to refine {file_path}: {e}", exc_info=True)
        
        logger.info(f"\nRefinement complete: {len(files)} file(s) processed")
