"""Configuration file loader for Gemini Powerpoint Sage.

Supports loading configuration from YAML files to simplify
command-line usage and enable easier review/sharing of settings.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

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
        has_input_folder = "input_folder" in config and config["input_folder"]

        input_methods = sum([bool(has_pptx), bool(has_folder), bool(has_input_folder)])
        
        if input_methods == 0:
            raise ValueError(
                "Configuration must specify either 'pptx', 'folder', or 'input_folder'"
            )

        if input_methods > 1:
            raise ValueError(
                "Configuration cannot specify multiple input methods (pptx, folder, input_folder)"
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

        if has_input_folder:
            folder_path = config["input_folder"]
            if not os.path.isdir(folder_path):
                raise ValueError(f"Input folder not found: {folder_path}")
            
            # Validate PDF/PPTX pairs exist
            ConfigFileLoader._validate_file_pairs(folder_path)

        # Validate PDF if specified
        if "pdf" in config and config["pdf"]:
            pdf_path = config["pdf"]
            if not os.path.exists(pdf_path):
                raise ValueError(f"PDF file not found: {pdf_path}")

    @staticmethod
    def _validate_file_pairs(folder_path: str) -> None:
        """
        Validate that PDF/PPTX pairs exist in the folder.
        
        Args:
            folder_path: Path to folder to validate
            
        Raises:
            ValueError: If no valid pairs are found
        """
        import glob
        
        # Find all PPTX files (case-insensitive)
        pptx_pattern = os.path.join(folder_path, "*.[Pp][Pp][Tt][Xx]")
        pptx_files = glob.glob(pptx_pattern)
        
        if not pptx_files:
            raise ValueError(f"No PPTX files found in folder: {folder_path}")
        
        valid_pairs = []
        missing_pdfs = []
        
        for pptx_file in pptx_files:
            # Get base name without extension
            base_name = os.path.splitext(pptx_file)[0]
            
            # Look for corresponding PDF (case-insensitive)
            pdf_candidates = [
                base_name + ".pdf",
                base_name + ".PDF"
            ]
            
            pdf_found = False
            for pdf_candidate in pdf_candidates:
                if os.path.exists(pdf_candidate):
                    valid_pairs.append((pptx_file, pdf_candidate))
                    pdf_found = True
                    break
            
            if not pdf_found:
                missing_pdfs.append(os.path.basename(pptx_file))
        
        if not valid_pairs:
            raise ValueError(
                f"No valid PDF/PPTX pairs found in folder: {folder_path}. "
                f"Each PPTX file must have a corresponding PDF with the same base name."
            )
        
        if missing_pdfs:
            logger.warning(
                f"PPTX files without matching PDFs (will be skipped): {', '.join(missing_pdfs)}"
            )
        
        logger.info(f"Found {len(valid_pairs)} valid PDF/PPTX pairs in {folder_path}")

    @staticmethod
    def get_file_pairs(folder_path: str) -> List[tuple]:
        """
        Get all valid PDF/PPTX pairs from a folder.
        
        Args:
            folder_path: Path to folder containing files
            
        Returns:
            List of (pptx_path, pdf_path) tuples
        """
        import glob
        
        pptx_pattern = os.path.join(folder_path, "*.[Pp][Pp][Tt][Xx]")
        pptx_files = glob.glob(pptx_pattern)
        
        pairs = []
        for pptx_file in pptx_files:
            base_name = os.path.splitext(pptx_file)[0]
            
            pdf_candidates = [
                base_name + ".pdf",
                base_name + ".PDF"
            ]
            
            for pdf_candidate in pdf_candidates:
                if os.path.exists(pdf_candidate):
                    pairs.append((pptx_file, pdf_candidate))
                    break
        
        return pairs

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
            "input_folder": "input_folder",
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

        # Set default language if neither config nor CLI provided it
        if "language" not in merged or merged["language"] is None:
            from config.constants import LanguageConfig
            merged["language"] = LanguageConfig.DEFAULT_LANGUAGE

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
        f.write('# input_folder: "path/to/folder"  # Auto-detects PDF/PPTX pairs\n')
        f.write('# folder: "path/to/folder"  # Legacy folder processing\n\n')
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
