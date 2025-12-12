"""Unified processor that consolidates all running methods.

Purely YAML-driven processor that handles style configurations
from YAML files without CLI overrides.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

from .input_scanner import FileSet, InputScanner
from config import Config
from config.config_loader import ConfigFileLoader
from services.presentation_processor import PresentationProcessor
from agents.agent_factory import create_all_agents
from utils.cli_utils import parse_languages

logger = logging.getLogger(__name__)


class UnifiedProcessor:
    """Unified processor for YAML-driven presentation processing."""
    
    def __init__(
        self,
        root_path: str = ".",
        course_id: Optional[str] = None,
        skip_visuals: bool = False,
        generate_videos: bool = False,
        retry_errors: bool = False,
        region: str = "global"
    ):
        """
        Initialize unified processor.
        
        Args:
            root_path: Root directory for scanning
            course_id: Optional course ID for context
            skip_visuals: Whether to skip visual generation
            generate_videos: Whether to generate videos
            retry_errors: Whether to retry slides with errors
            region: Google Cloud region
        """
        self.root_path = root_path
        self.course_id = course_id
        self.skip_visuals = skip_visuals
        self.generate_videos = generate_videos
        self.retry_errors = retry_errors
        self.region = region
        
        self.scanner = InputScanner(root_path)
        
    def _setup_environment(self) -> None:
        """Setup environment variables."""
        if self.retry_errors:
            os.environ["SPEAKER_NOTE_RETRY_ERRORS"] = "true"
        else:
            os.environ.pop("SPEAKER_NOTE_RETRY_ERRORS", None)
        
        if self.region:
            os.environ["GOOGLE_CLOUD_LOCATION"] = self.region
    
    def _parse_languages(self, languages: str) -> List[str]:
        """Parse and normalize language list."""
        return parse_languages(languages)
    
    async def process_single_file(
        self, 
        pptx_path: str, 
        pdf_path: Optional[str] = None,
        language: str = "en",
        style: str = "professional",
        output_dir: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Process a single PPTX file with explicit parameters.
        
        Args:
            pptx_path: Path to PPTX file
            pdf_path: Optional path to PDF file
            language: Language for processing
            style: Style for processing
            output_dir: Optional output directory
            
        Returns:
            Tuple of (notes_output_path, visuals_output_path)
        """
        # Resolve PDF path if not provided
        if not pdf_path:
            from utils.cli_utils import resolve_pdf_path, resolve_pptx_path
            pptx_abs = resolve_pptx_path(pptx_path)
            pdf_path = resolve_pdf_path(None, pptx_abs)
            
            if not pdf_path:
                raise ValueError(f"No matching PDF found for: {pptx_path}")
        
        # Create file set
        file_set = FileSet(
            pptx_path=pptx_path,
            pdf_path=pdf_path,
            base_name=os.path.splitext(os.path.basename(pptx_path))[0],
            directory=os.path.dirname(pptx_path),
            style=style
        )
        
        # Process languages
        lang_list = self._parse_languages(language)
        results = []
        
        for lang in lang_list:
            logger.info(f"Processing {file_set.base_name} - Language: {lang}")
            result = await self._process_single_file_set(file_set, lang, style, output_dir)
            results.append(result)
        
        return results[-1]  # Return last result
    
    async def process_styles_directory(self) -> Dict[str, Dict[str, List[Tuple[str, Optional[str]]]]]:
        """
        Process all files in styles directory with YAML configurations.
        
        Returns:
            Dictionary mapping styles to file processing results
        """
        self._setup_environment()
        
        file_sets = self.scanner.scan_styles()
        
        if not file_sets:
            logger.warning("No files found in styles directory")
            return {}
        
        # Organize by style
        by_style = self.scanner.organize_by_style(file_sets)
        results = {}
        
        for style_name, style_file_sets in by_style.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing style: {style_name}")
            logger.info(f"{'='*60}")
            
            # Load style configuration
            config_path = self.scanner.get_style_config_path(style_name)
            if config_path:
                logger.info(f"Loading YAML configuration: {config_path}")
                try:
                    style_config = ConfigFileLoader.load_from_file(config_path)
                    style_results = await self._process_file_sets_with_config(style_file_sets, style_config)
                    results[style_name] = style_results
                    
                except Exception as e:
                    logger.error(f"Error loading YAML config for {style_name}: {e}")
                    logger.error("Skipping this style due to configuration error")
                    continue
            else:
                logger.warning(f"No YAML configuration found for style: {style_name}")
                logger.warning("Skipping this style - YAML config required")
                continue
        
        return results
    
    async def process_single_style(self, style_identifier: str) -> Dict[str, List[Tuple[str, Optional[str]]]]:
        """
        Process files using a single style configuration.
        
        Args:
            style_identifier: Style name (e.g., 'cyberpunk') or full path to config file
            
        Returns:
            Dictionary mapping file names to processing results
        """
        self._setup_environment()
        
        # Determine config file path
        if os.path.isfile(style_identifier):
            # Full path provided
            config_path = style_identifier
            style_name = os.path.splitext(os.path.basename(style_identifier))[0]
            if style_name.startswith("config."):
                style_name = style_name.replace("config.", "")
        else:
            # Style name provided, find config file
            config_path = self.scanner.get_style_config_path(style_identifier)
            style_name = style_identifier
            
            if not config_path:
                raise ValueError(f"No configuration file found for style: {style_identifier}")
        
        logger.info(f"Processing single style: {style_name}")
        logger.info(f"Using configuration: {config_path}")
        
        # Load configuration
        try:
            style_config = ConfigFileLoader.load_from_file(config_path)
        except Exception as e:
            raise ValueError(f"Error loading configuration file {config_path}: {e}")
        
        # Get input folder from config
        input_folder = style_config.get("input_folder")
        if not input_folder:
            raise ValueError(f"Configuration file {config_path} must specify 'input_folder'")
        
        # Scan for files in the specified input folder
        from pathlib import Path
        file_sets = self.scanner.scan_directory(Path(input_folder))
        
        if not file_sets:
            logger.warning(f"No PPTX/PDF pairs found in input folder: {input_folder}")
            return {}
        
        # Add style metadata to file sets
        for file_set in file_sets:
            file_set.style = style_name
            file_set.category = f"style/{style_name}"
        
        # Process files with the configuration
        logger.info(f"Found {len(file_sets)} file sets in {input_folder}")
        results = await self._process_file_sets_with_config(file_sets, style_config)
        
        return results
    
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
        config_skip_visuals = config.get("skip_visuals", self.skip_visuals)
        config_generate_videos = config.get("generate_videos", self.generate_videos)
        
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
                        file_set, lang, config
                    )
                    file_results.append(result)
                    logger.info(f"Successfully processed {file_set.base_name} ({lang})")
                except Exception as e:
                    logger.error(f"Error processing {file_set.base_name} ({lang}): {e}", exc_info=True)
                    continue
            
            results[file_set.base_name] = file_results
        
        return results
    
    async def _process_single_file_set(
        self, 
        file_set: FileSet, 
        language: str,
        style: str,
        output_dir: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Process a single file set for single-file mode.
        
        Args:
            file_set: File set to process
            language: Language to process
            style: Style to use
            output_dir: Optional output directory
            
        Returns:
            Tuple of (notes_output_path, visuals_output_path)
        """
        # Determine output directory
        effective_output_dir = output_dir or file_set.directory
        
        # Create configuration
        config = Config(
            pptx_path=file_set.pptx_path,
            pdf_path=file_set.pdf_path,
            course_id=self.course_id,
            skip_visuals=self.skip_visuals,
            generate_videos=self.generate_videos,
            language=language,
            style=style,
            output_dir=effective_output_dir,
        )
        
        # Validate configuration
        config.validate()
        
        # Create agents with styles
        agents = create_all_agents(
            visual_style=config.visual_style,
            speaker_style=config.speaker_style
        )
        
        # Create processor
        processor = PresentationProcessor(
            config=config,
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
    
    async def _process_file_set_with_config(
        self, 
        file_set: FileSet, 
        language: str, 
        config: Dict[str, any]
    ) -> Tuple[str, Optional[str]]:
        """
        Process a single file set using YAML configuration.
        
        Args:
            file_set: File set to process
            language: Language to process
            config: YAML configuration dictionary
            
        Returns:
            Tuple of (notes_output_path, visuals_output_path)
        """
        # Extract config values
        config_style = config.get("style")
        config_output_dir = config.get("output_dir")
        config_skip_visuals = config.get("skip_visuals", self.skip_visuals)
        config_generate_videos = config.get("generate_videos", self.generate_videos)
        
        # Use YAML config values
        effective_style = config_style or file_set.style
        effective_output_dir = config_output_dir or self.scanner.get_output_directory(file_set)
        
        # Create configuration
        config_obj = Config(
            pptx_path=file_set.pptx_path,
            pdf_path=file_set.pdf_path,
            course_id=self.course_id,
            skip_visuals=config_skip_visuals,
            generate_videos=config_generate_videos,
            language=language,
            style=effective_style,
            output_dir=effective_output_dir,
        )
        
        # Validate configuration
        config_obj.validate()
        
        # Create agents with styles
        agents = create_all_agents(
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