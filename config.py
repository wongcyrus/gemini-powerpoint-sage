"""Configuration management for Gemini Powerpoint Sage."""

import logging
import os
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """Central configuration for the Gemini Powerpoint Sage."""

    def __init__(
        self,
        pptx_path: str,
        pdf_path: str,
        course_id: Optional[str] = None,
        progress_file: Optional[str] = None,
        retry_errors: bool = False,
        region: str = "global",
        skip_visuals: bool = False,
        language: str = "en",
    ):
        """
        Initialize configuration.

        Args:
            pptx_path: Path to input PowerPoint file
            pdf_path: Path to input PDF file
            course_id: Optional course ID for context
            progress_file: Optional custom progress file path
            retry_errors: Whether to retry slides with errors
            region: Google Cloud region
            skip_visuals: Whether to skip visual generation
            language: Language locale code (e.g., en, zh-CN, yue-HK)
        """
        self.pptx_path = pptx_path
        self.pdf_path = pdf_path
        self.course_id = course_id
        self.progress_file = progress_file
        self.retry_errors = retry_errors
        self.region = region
        self.skip_visuals = skip_visuals
        self.language = language

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Apply configuration from environment variables."""
        if self.progress_file:
            os.environ["SPEAKER_NOTE_PROGRESS_FILE"] = self.progress_file

        if self.retry_errors:
            os.environ["SPEAKER_NOTE_RETRY_ERRORS"] = "true"

        # Set Google Cloud Location
        if self.region:
            os.environ["GOOGLE_CLOUD_LOCATION"] = self.region
        elif "GOOGLE_CLOUD_LOCATION" not in os.environ:
            os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

    @property
    def output_path(self) -> str:
        """Get the output path for the presentation with notes only."""
        pptx_dir = os.path.dirname(self.pptx_path)
        pptx_base = os.path.splitext(os.path.basename(self.pptx_path))[0]
        generate_dir = os.path.join(pptx_dir, "generate")
        os.makedirs(generate_dir, exist_ok=True)
        return os.path.join(generate_dir, f"{pptx_base}_{self.language}_with_notes.pptx")

    @property
    def output_path_with_visuals(self) -> str:
        """Get the output path for the presentation with visuals."""
        pptx_dir = os.path.dirname(self.pptx_path)
        pptx_base = os.path.splitext(os.path.basename(self.pptx_path))[0]
        generate_dir = os.path.join(pptx_dir, "generate")
        os.makedirs(generate_dir, exist_ok=True)
        return os.path.join(generate_dir, f"{pptx_base}_{self.language}_with_visuals.pptx")

    @property
    def visuals_dir(self) -> str:
        """Get the directory for storing visual outputs."""
        pptx_dir = os.path.dirname(self.pptx_path)
        pptx_base = os.path.splitext(os.path.basename(self.pptx_path))[0]
        generate_dir = os.path.join(pptx_dir, "generate")
        return os.path.join(generate_dir, f"{pptx_base}_{self.language}_visuals")

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If validation fails
        """
        if not os.path.exists(self.pptx_path):
            raise ValueError(f"PPTX file not found: {self.pptx_path}")

        if not os.path.exists(self.pdf_path):
            raise ValueError(f"PDF file not found: {self.pdf_path}")

        return True

    def get_presentation_theme(self) -> str:
        """
        Get the presentation theme based on course configuration.

        Returns:
            Theme description string
        """
        if not self.course_id:
            return "General Presentation"

        try:
            # Dynamically import to avoid circular imports
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            if project_root not in sys.path:
                sys.path.append(project_root)

            from presentation_preloader.utils import course_utils

            course_config = course_utils.get_course_config(self.course_id)
            if course_config:
                return (
                    course_config.get("description")
                    or course_config.get("name")
                    or f"Course {self.course_id}"
                )
        except Exception as e:
            logger.warning(
                f"Failed to fetch course config for {self.course_id}: {e}"
            )

        return f"Course {self.course_id}"

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"Config(pptx={self.pptx_path}, pdf={self.pdf_path}, "
            f"course_id={self.course_id}, region={self.region}, "
            f"skip_visuals={self.skip_visuals}, language={self.language})"
        )
