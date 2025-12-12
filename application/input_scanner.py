"""Input scanner for discovering and organizing presentation files.

Provides a unified approach to scanning for PPTX/PDF pairs across
different directory structures including styles/ and notes/ folders.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class FileSet:
    """Represents a matched PPTX/PDF pair with metadata."""
    pptx_path: str
    pdf_path: str
    base_name: str
    directory: str
    style: Optional[str] = None
    category: Optional[str] = None


class InputScanner:
    """Scans directories for presentation files with 2-level organization."""
    
    def __init__(self, root_path: str):
        """
        Initialize scanner.
        
        Args:
            root_path: Root directory to scan from
        """
        self.root_path = Path(root_path).resolve()
        
    def scan_all(self) -> Dict[str, List[FileSet]]:
        """
        Scan all supported directory structures.
        
        Returns:
            Dictionary mapping scan type to list of file sets
        """
        results = {}
        
        # Scan styles directory
        styles_files = self.scan_styles()
        if styles_files:
            results["styles"] = styles_files
            
        # Scan notes directory  
        notes_files = self.scan_notes()
        if notes_files:
            results["notes"] = notes_files
            
        # Scan root directory
        root_files = self.scan_directory(self.root_path)
        if root_files:
            results["root"] = root_files
            
        return results
    
    def scan_styles(self) -> List[FileSet]:
        """
        Scan styles directory for organized presentation files.
        
        Expected structure:
        styles/
        ├── config.{style}.yaml
        └── {style}/
            ├── input/
            │   ├── presentation.pptx
            │   └── presentation.pdf
            └── generate/  (output)
        
        Returns:
            List of file sets found in styles directories
        """
        styles_dir = self.root_path / "styles"
        if not styles_dir.exists():
            return []
            
        file_sets = []
        
        # Look for style subdirectories
        for style_path in styles_dir.iterdir():
            if not style_path.is_dir():
                continue
                
            style_name = style_path.name
            
            # Skip common non-style directories
            if style_name in ["__pycache__", ".git", "generate"]:
                continue
                
            # Look for input directory
            input_dir = style_path / "input"
            if input_dir.exists():
                sets = self.scan_directory(input_dir, style=style_name, category="styles")
                file_sets.extend(sets)
            else:
                # Also check style directory directly
                sets = self.scan_directory(style_path, style=style_name, category="styles")
                file_sets.extend(sets)
                
        logger.info(f"Found {len(file_sets)} file sets in styles directory")
        return file_sets
    
    def scan_notes(self) -> List[FileSet]:
        """
        Scan notes directory for presentation files.
        
        Expected structure:
        notes/
        ├── {category}/
        │   ├── presentation1.pptx
        │   ├── presentation1.pdf
        │   ├── presentation2.pptx
        │   └── presentation2.pdf
        └── presentation3.pptx
        └── presentation3.pdf
        
        Returns:
            List of file sets found in notes directories
        """
        notes_dir = self.root_path / "notes"
        if not notes_dir.exists():
            return []
            
        file_sets = []
        
        # Scan root notes directory
        root_sets = self.scan_directory(notes_dir, category="notes")
        file_sets.extend(root_sets)
        
        # Scan subdirectories
        for subdir in notes_dir.iterdir():
            if not subdir.is_dir():
                continue
                
            category_name = subdir.name
            
            # Skip common non-category directories
            if category_name in ["__pycache__", ".git"]:
                continue
                
            sets = self.scan_directory(subdir, category=f"notes/{category_name}")
            file_sets.extend(sets)
                
        logger.info(f"Found {len(file_sets)} file sets in notes directory")
        return file_sets
    
    def scan_directory(
        self, 
        directory: Path, 
        style: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[FileSet]:
        """
        Scan a single directory for PPTX/PDF pairs.
        
        Args:
            directory: Directory to scan
            style: Optional style name for metadata
            category: Optional category name for metadata
            
        Returns:
            List of file sets found
        """
        if not directory.exists() or not directory.is_dir():
            return []
            
        file_sets = []
        pptx_files = []
        
        # Find all PPTX files (case-insensitive)
        for pattern in ["*.pptx", "*.PPTX", "*.pptm", "*.PPTM"]:
            pptx_files.extend(directory.glob(pattern))
        
        # Filter out temporary files
        pptx_files = [f for f in pptx_files if not f.name.startswith('~')]
        
        for pptx_file in pptx_files:
            # Look for corresponding PDF
            base_name = pptx_file.stem
            pdf_candidates = [
                directory / f"{base_name}.pdf",
                directory / f"{base_name}.PDF"
            ]
            
            pdf_file = None
            for candidate in pdf_candidates:
                if candidate.exists():
                    pdf_file = candidate
                    break
            
            if pdf_file:
                file_set = FileSet(
                    pptx_path=str(pptx_file),
                    pdf_path=str(pdf_file),
                    base_name=base_name,
                    directory=str(directory),
                    style=style,
                    category=category
                )
                file_sets.append(file_set)
            else:
                logger.warning(f"No matching PDF found for: {pptx_file.name}")
        
        return file_sets
    
    def get_style_config_path(self, style_name: str) -> Optional[str]:
        """
        Get the configuration file path for a style.
        
        Args:
            style_name: Name of the style
            
        Returns:
            Path to config file if found, None otherwise
        """
        styles_dir = self.root_path / "styles"
        if not styles_dir.exists():
            return None
            
        config_candidates = [
            styles_dir / f"config.{style_name.lower()}.yaml",
            styles_dir / f"config.{style_name.lower()}.yml",
            styles_dir / f"{style_name.lower()}.config.yaml",
            styles_dir / f"{style_name.lower()}.config.yml"
        ]
        
        for candidate in config_candidates:
            if candidate.exists():
                return str(candidate)
                
        return None
    
    def organize_by_style(self, file_sets: List[FileSet]) -> Dict[str, List[FileSet]]:
        """
        Organize file sets by style.
        
        Args:
            file_sets: List of file sets to organize
            
        Returns:
            Dictionary mapping style names to file sets
        """
        organized = {}
        
        for file_set in file_sets:
            style = file_set.style or "default"
            if style not in organized:
                organized[style] = []
            organized[style].append(file_set)
            
        return organized
    
    def get_output_directory(self, file_set: FileSet, base_output_dir: Optional[str] = None) -> str:
        """
        Determine appropriate output directory for a file set.
        
        Args:
            file_set: File set to get output directory for
            base_output_dir: Optional base output directory override
            
        Returns:
            Output directory path
        """
        if base_output_dir:
            return base_output_dir
            
        # For styles, use generate subdirectory
        if file_set.style and file_set.category == "styles":
            styles_dir = self.root_path / "styles" / file_set.style / "generate"
            return str(styles_dir)
            
        # For notes, use same directory as input
        if file_set.category and file_set.category.startswith("notes"):
            return file_set.directory
            
        # Default to input directory
        return file_set.directory


def scan_input_sources(root_path: str = ".") -> Dict[str, List[FileSet]]:
    """
    Convenience function to scan all input sources.
    
    Args:
        root_path: Root directory to scan from
        
    Returns:
        Dictionary mapping source types to file sets
    """
    scanner = InputScanner(root_path)
    return scanner.scan_all()