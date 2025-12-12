"""Configuration management for Gemini Powerpoint Sage."""

import logging
import os
import sys
from typing import Optional

from config.constants import EnvironmentVars, FilePatterns

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
        generate_videos: bool = False,
        language: str = "en",
        style: Optional[str] = None,
        output_dir: Optional[str] = None,
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
            generate_videos: Whether to generate videos for slides
            language: Language locale code (e.g., en, zh-CN, yue-HK)
            style: Optional style/theme for content generation (e.g., "Gundam", "Cyberpunk", "Minimalist")
            output_dir: Optional output directory (defaults to generate/ folder next to input)
        """
        self.pptx_path = pptx_path
        self.pdf_path = pdf_path
        self.course_id = course_id
        self.progress_file = progress_file
        self.retry_errors = retry_errors
        self.region = region
        self.skip_visuals = skip_visuals
        self.generate_videos = generate_videos
        self.language = language
        self.output_dir = output_dir
        
        # Handle style - can be a string or dict with visual_style and speaker_style
        if isinstance(style, dict):
            self.visual_style = style.get("visual_style", "professional")
            self.speaker_style = style.get("speaker_style", "professional")
            self.style = style.get("visual_style", "professional")  # For filename generation
        else:
            # Single style applies to both
            default_style = style or os.getenv("PRESENTATION_STYLE", "professional")
            self.visual_style = default_style
            self.speaker_style = default_style
            self.style = default_style

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Apply configuration from environment variables."""
        if self.progress_file:
            os.environ[EnvironmentVars.PROGRESS_FILE] = self.progress_file

        if self.retry_errors:
            os.environ[EnvironmentVars.RETRY_ERRORS] = "true"

        # Set Google Cloud Location
        if self.region:
            os.environ[EnvironmentVars.GOOGLE_CLOUD_LOCATION] = self.region
        elif EnvironmentVars.GOOGLE_CLOUD_LOCATION not in os.environ:
            os.environ[EnvironmentVars.GOOGLE_CLOUD_LOCATION] = "global"

    def _get_output_dir(self) -> str:
        """
        Get the output directory, creating it if needed.
        
        If output_dir is specified, use it directly.
        Otherwise, create a style-specific subfolder in generate/:
        - generate/cyberpunk/ for cyberpunk style
        - generate/gundam/ for gundam style
        - generate/ for professional style (default)
        """
        pptx_dir = os.path.dirname(self.pptx_path)
        
        if self.output_dir:
            # User specified custom output directory - use it directly
            output_dir = self.output_dir
        else:
            # Default behavior: organize by style in generate/ folder
            base_dir = os.path.join(pptx_dir, "generate")
            
            # Create style-specific subfolder if not professional
            if self.style and self.style.lower() != "professional":
                style_folder = self.style.replace(" ", "_").lower()
                output_dir = os.path.join(base_dir, style_folder)
            else:
                # professional style goes directly in generate/
                output_dir = base_dir
        
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    @property
    def output_path(self) -> str:
        """
        Get the output path for the presentation with notes only.
        
        DEPRECATED: Use Presentation.get_output_path() for style-aware naming.
        This property is kept for backward compatibility.
        """
        from pathlib import Path
        from core.domain.presentation import Presentation
        
        # Create a temporary presentation object to use its naming logic
        pres = Presentation(
            pptx_path=Path(self.pptx_path),
            pdf_path=Path(self.pdf_path),
            language=self.language,
            style=self.style
        )
        
        output_dir = Path(self._get_output_dir())
        return str(pres.get_output_path(suffix="_notes", output_dir=output_dir))

    @property
    def output_path_with_visuals(self) -> str:
        """
        Get the output path for the presentation with visuals.
        
        DEPRECATED: Use Presentation.get_output_path() for style-aware naming.
        This property is kept for backward compatibility.
        """
        from pathlib import Path
        from core.domain.presentation import Presentation
        
        # Create a temporary presentation object to use its naming logic
        pres = Presentation(
            pptx_path=Path(self.pptx_path),
            pdf_path=Path(self.pdf_path),
            language=self.language,
            style=self.style
        )
        
        output_dir = Path(self._get_output_dir())
        return str(pres.get_output_path(suffix="_visuals", output_dir=output_dir))

    @property
    def visuals_dir(self) -> str:
        """Get the directory for storing visual outputs."""
        pptx_base = os.path.splitext(os.path.basename(self.pptx_path))[0]
        output_dir = self._get_output_dir()
        
        # Build directory name with language (always include language code)
        dirname = FilePatterns.VISUALS_DIR.format(
            base=pptx_base,
            lang=self.language
        )
        return os.path.join(output_dir, dirname)

    @property
    def videos_dir(self) -> str:
        """Get the directory for storing video outputs."""
        pptx_base = os.path.splitext(os.path.basename(self.pptx_path))[0]
        output_dir = self._get_output_dir()
        
        # Build directory name with language (always include language code)
        dirname = FilePatterns.VIDEOS_DIR.format(
            base=pptx_base,
            lang=self.language
        )
        videos_dir = os.path.join(output_dir, dirname)
        os.makedirs(videos_dir, exist_ok=True)
        return videos_dir

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
            f"skip_visuals={self.skip_visuals}, language={self.language}, "
            f"visual_style={self.visual_style}, speaker_style={self.speaker_style})"
        )
