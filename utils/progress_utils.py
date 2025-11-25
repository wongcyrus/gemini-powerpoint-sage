"""Progress tracking utilities for Gemini Powerpoint Sage."""

import hashlib
import json
import logging
import os
import tempfile
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_progress(path: str) -> Dict[str, Any]:
    """
    Load progress data from a JSON file.
    
    Args:
        path: Path to the progress file
        
    Returns:
        Dictionary containing progress data, or empty structure if file doesn't exist
    """
    if not os.path.exists(path):
        return {"slides": {}}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load progress file: {e}")
        return {"slides": {}}


def save_progress(path: str, data: Dict[str, Any]) -> None:
    """
    Save progress data to a JSON file atomically.
    
    Uses atomic file replacement to prevent corruption.
    
    Args:
        path: Path to the progress file
        data: Dictionary containing progress data
    """
    try:
        target_dir = os.path.dirname(path) or "."
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix="sn_prog_", 
            suffix=".json", 
            dir=target_dir
        )
        
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        os.replace(tmp_path, path)
        logger.debug(f"Progress saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save progress file: {e}")


def create_slide_key(index: int, notes: str) -> str:
    """
    Create a unique key for a slide based on its index and notes.
    
    The key includes a hash of the notes to detect when notes have changed.
    
    Args:
        index: Slide index (1-based)
        notes: Existing notes text
        
    Returns:
        Unique slide key string
    """
    h = hashlib.sha256((notes or "").encode("utf-8")).hexdigest()[:8]
    return f"slide_{index}_{h}"


def get_progress_file_path(pptx_path: str) -> str:
    """
    Determine the progress file path.
    
    Checks environment variable first, then defaults to same directory as PPTX.
    
    Args:
        pptx_path: Path to the PowerPoint file
        
    Returns:
        Path to the progress file
    """
    progress_file = os.environ.get("SPEAKER_NOTE_PROGRESS_FILE")
    if not progress_file:
        progress_file = os.getenv("SPEAKER_NOTE_PROGRESS_FILE")
    
    if not progress_file:
        progress_file = os.path.join(
            os.path.dirname(pptx_path), 
            "speaker_note_progress.json"
        )
    
    return progress_file


def should_retry_errors() -> bool:
    """
    Check if error retry mode is enabled.
    
    Returns:
        True if errors should be retried
    """
    return os.environ.get("SPEAKER_NOTE_RETRY_ERRORS", "false").lower() == "true"
