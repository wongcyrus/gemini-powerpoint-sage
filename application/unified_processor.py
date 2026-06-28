"""Unified processor for YAML-defined presentation runs."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .input_scanner import FileSet, InputScanner
from config import Config
from config.config_loader import ConfigFileLoader
from services.presentation_processor import PresentationProcessor
from agents.agent_factory import create_all_agents
from utils.cli_utils import parse_languages

logger = logging.getLogger(__name__)


class UnifiedProcessor:
    """Unified processor for YAML-driven presentation processing."""
    
    def __init__(self, root_path: str = "."):
        """
        Initialize unified processor.
        
        Args:
            root_path: Root directory for scanning
        """
        self.root_path = root_path

        self.scanner = InputScanner(root_path)
    
    def _parse_languages(self, languages: str) -> List[str]:
        """Parse and normalize language list."""
        return parse_languages(languages)
    
    async def process_styles_directory(self) -> Dict[str, Dict[str, List[Tuple[str, Optional[str]]]]]:
        """
        Process all files in styles directory with YAML configurations.
        
        Returns:
            Dictionary mapping styles to file processing results
        """
        config_paths = self.scanner.get_style_config_paths()

        if not config_paths:
            logger.warning("No YAML style configurations found in styles directory")
            return {}

        results = {}
        for config_path in config_paths:
            style_name = self._get_style_name(config_path)
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing style: {style_name}")
            logger.info(f"{'='*60}")

            try:
                results[style_name] = await self.process_single_style(config_path)
            except Exception as e:
                logger.error(f"Error loading YAML config for {style_name}: {e}")
                logger.error("Skipping this style due to configuration error")

        return results
    
    async def process_single_style(self, style_identifier: str) -> Dict[str, List[Tuple[str, Optional[str]]]]:
        """
        Process files using a single style configuration.
        
        Args:
            style_identifier: Style name (e.g., 'cyberpunk') or full path to config file
            
        Returns:
            Dictionary mapping file names to processing results
        """
        config_path = self._resolve_style_config_path(style_identifier)
        style_name = self._get_style_name(config_path)

        logger.info(f"Processing single style: {style_name}")
        logger.info(f"Using configuration: {config_path}")
        return await self.process_config(config_path)

    async def process_config(self, config_identifier: str) -> Dict[str, List[Tuple[str, Optional[str]]]]:
        """Process presentations described by a config file."""
        config_path = self._resolve_style_config_path(config_identifier)

        try:
            config = ConfigFileLoader.load_from_file(config_path)
        except Exception as e:
            raise ValueError(f"Error loading configuration file {config_path}: {e}")

        style_name = self._get_style_name(config_path)
        file_sets = self._get_file_sets_from_config(config, style_name)

        if not file_sets:
            input_folder = config.get("input_folder") or config.get("folder")
            logger.warning(f"No PPTX/PDF pairs found in input folder: {input_folder}")
            return {}

        logger.info(f"Found {len(file_sets)} file sets for config {config_path}")
        return await self._process_file_sets_with_config(file_sets, config)

    def _resolve_style_config_path(self, style_identifier: str) -> str:
        """Resolve a style name or file path to a config file path."""
        if os.path.isfile(style_identifier):
            return style_identifier

        config_path = self.scanner.get_style_config_path(style_identifier)
        if not config_path:
            raise ValueError(f"No configuration file found for style: {style_identifier}")
        return config_path

    def _get_style_name(self, config_path: str) -> str:
        """Infer the style name from a config file path."""
        style_name = os.path.splitext(os.path.basename(config_path))[0]
        if style_name.startswith("config."):
            return style_name.replace("config.", "")
        if style_name.endswith(".config"):
            return style_name.replace(".config", "")
        return style_name

    def _get_file_sets_from_config(
        self, config: Dict[str, Any], style_name: Optional[str] = None
    ) -> List[FileSet]:
        """Create file sets from a resolved config dictionary."""
        pptx_path = config.get("pptx")
        if pptx_path:
            pdf_path = config.get("pdf")
            if not pdf_path:
                from utils.cli_utils import resolve_pdf_path

                pdf_path = resolve_pdf_path(None, pptx_path)
                if not pdf_path:
                    raise ValueError(f"No matching PDF found for: {pptx_path}")

            pptx_path_obj = Path(pptx_path)
            return [
                FileSet(
                    pptx_path=str(pptx_path_obj),
                    pdf_path=str(pdf_path),
                    base_name=pptx_path_obj.stem,
                    directory=str(pptx_path_obj.parent),
                    style=style_name,
                    category=f"style/{style_name}" if style_name else "config",
                )
            ]

        input_folder = config.get("input_folder") or config.get("folder")
        if not input_folder:
            raise ValueError("Configuration file must specify 'pptx', 'folder', or 'input_folder'")

        file_sets = self.scanner.scan_directory(Path(input_folder))
        for file_set in file_sets:
            file_set.style = style_name or file_set.style
            file_set.category = f"style/{style_name}" if style_name else "config"
        return file_sets
    
    async def _process_file_sets_with_config(
        self, 
        file_sets: List[FileSet], 
        config: Dict[str, any]
    ) -> Dict[str, List[Tuple[str, Optional[str]]]]:
        """
        Process a list of file sets using YAML configuration.
        
        Args:
            file_sets: List of file sets to process
            config: YAML configuration dictionary
            
        Returns:
            Dictionary mapping file names to processing results
        """
        # Extract config values
        config_languages = config.get("language", "en")
        config_style = config.get("style")
        config_output_dir = config.get("output_dir")
        config_skip_visuals = config.get("skip_visuals", False)
        config_generate_videos = config.get("generate_videos", False)
        config_retry_errors = config.get("retry_errors", False)
        config_region = config.get("region", "global")
        config_course_id = config.get("course_id")
        config_progress_file = config.get("progress_file")
        
        # Parse languages from config
        lang_list = self._parse_languages(config_languages)
        results = {}
        
        logger.info(f"Processing {len(file_sets)} file sets with YAML config")
        logger.info(f"Languages: {', '.join(lang_list)}")
        if config_style:
            logger.info(f"Style: {config_style}")
        if config_output_dir:
            logger.info(f"Output directory: {config_output_dir}")
        
        for idx, file_set in enumerate(file_sets, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing file {idx}/{len(file_sets)}: {file_set.base_name}")
            logger.info(f"{'='*60}")
            
            file_results = []
            
            for lang in lang_list:
                logger.info(f"\n--- Processing language: {lang} ---")
                
                try:
                    result = await self._process_file_set_with_config(
                        file_set,
                        lang,
                        config_style=config_style,
                        config_output_dir=config_output_dir,
                        config_skip_visuals=config_skip_visuals,
                        config_generate_videos=config_generate_videos,
                        config_retry_errors=config_retry_errors,
                        config_region=config_region,
                        config_course_id=config_course_id,
                        config_progress_file=config_progress_file,
                    )
                    file_results.append(result)
                    logger.info(f"Successfully processed {file_set.base_name} ({lang})")
                except Exception as e:
                    logger.error(f"Error processing {file_set.base_name} ({lang}): {e}", exc_info=True)
                    continue
            
            results[file_set.base_name] = file_results
        
        return results
    
    async def _process_file_set_with_config(
        self, 
        file_set: FileSet, 
        language: str,
        *,
        config_style: Any,
        config_output_dir: Optional[str],
        config_skip_visuals: bool,
        config_generate_videos: bool,
        config_retry_errors: bool,
        config_region: str,
        config_course_id: Optional[str],
        config_progress_file: Optional[str],
    ) -> Tuple[str, Optional[str]]:
        """
        Process a single file set using YAML configuration.
        
        Args:
            file_set: File set to process
            language: Language to process
        Returns:
            Tuple of (notes_output_path, visuals_output_path)
        """
        # Use YAML config values
        effective_style = config_style or file_set.style
        effective_output_dir = config_output_dir or self.scanner.get_output_directory(file_set)
        
        # Create configuration
        config_obj = Config(
            pptx_path=file_set.pptx_path,
            pdf_path=file_set.pdf_path,
            course_id=config_course_id,
            progress_file=config_progress_file,
            retry_errors=config_retry_errors,
            region=config_region,
            skip_visuals=config_skip_visuals,
            generate_videos=config_generate_videos,
            language=language,
            style=effective_style,
            output_dir=effective_output_dir,
        )
        
        # Validate configuration
        config_obj.validate()
        
        # Create agents with styles
        agents = await create_all_agents(
            visual_style=config_obj.visual_style,
            speaker_style=config_obj.speaker_style
        )
        
        # Create processor
        processor = PresentationProcessor(
            config=config_obj,
            supervisor_agent=agents["supervisor"],
            analyst_agent=agents["analyst"],
            writer_agent=agents["writer"],
            auditor_agent=agents["auditor"],
            overviewer_agent=agents["overviewer"],
            designer_agent=agents["designer"],
            translator_agent=agents["translator"],
            image_translator_agent=agents["image_translator"],
            video_generator_agent=agents["video_generator"],
        )
        
        # Process presentation
        output_path_notes, output_path_visuals = await processor.process()
        
        return output_path_notes, output_path_visuals