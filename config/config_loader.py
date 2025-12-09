"""Configuration file loader for Gemini Powerpoint Sage.

Supports loading configuration from YAML files to simplify
command-line usage and enable easier review/sharing of settings.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ConfigFileLoader:
    """Loads configuration from YAML files."""

    @staticmethod
    def load_from_file(config_path: str) -> Dict[str, Any]:
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to configuration file (.yaml or .yml)

        Returns:
            Dictionary of configuration parameters

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is unsupported or invalid
            ImportError: If PyYAML is not installed
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        suffix = config_path.suffix.lower()

        if suffix not in [".yaml", ".yml"]:
            raise ValueError(
                f"Unsupported config file format: {suffix}. "
                "Use .yaml or .yml"
            )

        return ConfigFileLoader._load_yaml(config_path)

    @staticmethod
    def _load_yaml(config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required to load YAML config files. "
                "Install it with: pip install pyyaml"
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from YAML: {config_path}")
            return config or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """
        Validate configuration parameters.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Check for required parameters (at least one input method)
        has_pptx = "pptx" in config and config["pptx"]
        has_folder = "folder" in config and config["folder"]

        if not has_pptx and not has_folder:
            raise ValueError(
                "Configuration must specify either 'pptx' or 'folder'"
            )

        if has_pptx and has_folder:
            raise ValueError(
                "Configuration cannot specify both 'pptx' and 'folder'"
            )

        # Validate file paths exist
        if has_pptx:
            pptx_path = config["pptx"]
            if not os.path.exists(pptx_path):
                raise ValueError(f"PPTX file not found: {pptx_path}")

        if has_folder:
            folder_path = config["folder"]
            if not os.path.isdir(folder_path):
                raise ValueError(f"Folder not found: {folder_path}")

        # Validate PDF if specified
        if "pdf" in config and config["pdf"]:
            pdf_path = config["pdf"]
            if not os.path.exists(pdf_path):
                raise ValueError(f"PDF file not found: {pdf_path}")

    @staticmethod
    def merge_with_args(
        config: Dict[str, Any], args: Any
    ) -> Dict[str, Any]:
        """
        Merge configuration file with command-line arguments.
        Command-line arguments take precedence over config file.

        Args:
            config: Configuration from file
            args: Parsed command-line arguments

        Returns:
            Merged configuration dictionary
        """
        merged = config.copy()

        # Override with command-line arguments if provided
        arg_mappings = {
            "pptx": "pptx",
            "folder": "folder",
            "pdf": "pdf",
            "course_id": "course_id",
            "progress_file": "progress_file",
            "retry_errors": "retry_errors",
            "region": "region",
            "skip_visuals": "skip_visuals",
            "generate_videos": "generate_videos",
            "language": "language",
            "style": "style",
            "output_dir": "output_dir",
        }

        for arg_name, config_key in arg_mappings.items():
            arg_value = getattr(args, arg_name, None)
            # Override if argument was explicitly provided
            if arg_value is not None:
                # For boolean flags, check if they're True
                if isinstance(arg_value, bool):
                    if arg_value:
                        merged[config_key] = arg_value
                else:
                    merged[config_key] = arg_value

        return merged


def create_example_config(output_path: str) -> None:
    """
    Create an example YAML configuration file.

    Args:
        output_path: Path where to save the example config
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required. Install it with: pip install pyyaml"
        )

    with open(output_path, "w", encoding="utf-8") as f:
        # Write with comments
        f.write("# Gemini Powerpoint Sage Configuration\n\n")
        f.write("# Single file processing\n")
        f.write('pptx: "path/to/presentation.pptx"\n')
        f.write(
            'pdf: "path/to/presentation.pdf"  # Optional if same name as PPTX\n\n'
        )
        f.write("# OR folder processing (comment out pptx/pdf above)\n")
        f.write('# folder: "path/to/folder"\n\n')
        f.write("# Optional parameters\n")
        f.write("# course_id: null\n")
        f.write('region: "global"\n')
        f.write('language: "en"  # Or comma-separated: "en,zh-CN,yue-HK"\n')
        f.write(
            'style: "Professional"  # Gundam, Cyberpunk, Minimalist, etc.\n\n'
        )
        f.write("# Output directory (optional)\n")
        f.write("# Recommended pattern: {style}/generate/\n")
        f.write('# Examples: "cyberpunk/generate", "gundam/generate"\n')
        f.write('# output_dir: "cyberpunk/generate"\n\n')
        f.write("# Flags\n")
        f.write("skip_visuals: false\n")
        f.write("generate_videos: false\n")
        f.write("retry_errors: false\n\n")
        f.write("# Advanced\n")
        f.write("# progress_file: null\n")

    logger.info(f"Created example configuration file: {output_path}")
