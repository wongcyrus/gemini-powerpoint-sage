#!/usr/bin/env python3
"""
Migration script to move speech files from cache/speech to output structure.

This script moves existing speech files from the old cache/speech structure
to the new output/[style]/generate structure to match visual content organization.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_speech_directory_name(dir_name: str) -> Tuple[str, str]:
    """
    Parse speech directory name to extract presentation and language.
    
    Args:
        dir_name: Directory name like "Module 4a Cybersecurity Essentials - Information Security Concepts_en_speech"
        
    Returns:
        Tuple of (presentation_name, language_code)
    """
    if not dir_name.endswith('_speech'):
        raise ValueError(f"Invalid speech directory name: {dir_name}")
    
    # Remove _speech suffix
    base_name = dir_name[:-8]  # Remove "_speech"
    
    # Find the last underscore to separate language code
    parts = base_name.rsplit('_', 1)
    if len(parts) != 2:
        raise ValueError(f"Cannot parse language from directory name: {dir_name}")
    
    presentation_name, language_code = parts
    return presentation_name, language_code


def determine_style_from_presentation(presentation_name: str) -> str:
    """
    Determine the style based on presentation name or existing output structure.
    
    Args:
        presentation_name: Name of the presentation
        
    Returns:
        Style name (e.g., 'professional', 'cyberpunk', 'gundam')
    """
    # Check if there are existing visual outputs to determine style
    output_dir = Path("output")
    if not output_dir.exists():
        return "professional"  # Default style
    
    # Look for existing visual outputs for this presentation
    for style_dir in output_dir.iterdir():
        if not style_dir.is_dir():
            continue
            
        generate_dir = style_dir / "generate"
        if not generate_dir.exists():
            continue
            
        # Check if this presentation exists in this style
        for item in generate_dir.iterdir():
            if item.is_dir() and presentation_name in item.name and "_visuals" in item.name:
                logger.info(f"Found existing visuals for '{presentation_name}' in style '{style_dir.name}'")
                return style_dir.name
    
    # If no existing visuals found, default to professional
    logger.info(f"No existing visuals found for '{presentation_name}', using professional style")
    return "professional"


def migrate_speech_directory(
    old_dir: Path,
    presentation_name: str,
    language_code: str,
    style: str,
    dry_run: bool = False
) -> bool:
    """
    Migrate a single speech directory to the new structure.
    
    Args:
        old_dir: Path to old speech directory
        presentation_name: Name of the presentation
        language_code: Language code
        style: Style name
        dry_run: If True, only show what would be done
        
    Returns:
        True if migration was successful
    """
    # Determine new directory path
    if style.lower() == "professional":
        new_base_dir = Path("output") / "professional" / "generate"
    else:
        new_base_dir = Path("output") / style / "generate"
    
    new_dir_name = f"{presentation_name}_{language_code}_speech"
    new_dir = new_base_dir / new_dir_name
    
    logger.info(f"Migrating: {old_dir} -> {new_dir}")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would create directory: {new_dir}")
        logger.info(f"[DRY RUN] Would copy {len(list(old_dir.glob('*.mp3')))} MP3 files")
        return True
    
    try:
        # Create new directory structure
        new_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all MP3 files
        mp3_files = list(old_dir.glob("*.mp3"))
        copied_count = 0
        
        for mp3_file in mp3_files:
            new_file_path = new_dir / mp3_file.name
            
            # Skip if file already exists and is the same size
            if new_file_path.exists() and new_file_path.stat().st_size == mp3_file.stat().st_size:
                logger.debug(f"Skipping existing file: {mp3_file.name}")
                continue
            
            shutil.copy2(mp3_file, new_file_path)
            copied_count += 1
            logger.debug(f"Copied: {mp3_file.name}")
        
        logger.info(f"✓ Successfully migrated {copied_count} files to {new_dir}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to migrate {old_dir}: {e}")
        return False


def migrate_all_speech_files(dry_run: bool = False, cleanup: bool = False) -> Dict[str, int]:
    """
    Migrate all speech files from cache/speech to output structure.
    
    Args:
        dry_run: If True, only show what would be done
        cleanup: If True, remove old files after successful migration
        
    Returns:
        Dictionary with migration statistics
    """
    cache_speech_dir = Path("cache/speech")
    
    if not cache_speech_dir.exists():
        logger.info("No cache/speech directory found - nothing to migrate")
        return {"total": 0, "successful": 0, "failed": 0}
    
    stats = {"total": 0, "successful": 0, "failed": 0}
    
    # Find all speech directories
    speech_dirs = [d for d in cache_speech_dir.iterdir() if d.is_dir() and d.name.endswith('_speech')]
    
    if not speech_dirs:
        logger.info("No speech directories found in cache/speech")
        return stats
    
    logger.info(f"Found {len(speech_dirs)} speech directories to migrate")
    
    for speech_dir in speech_dirs:
        stats["total"] += 1
        
        try:
            # Parse directory name
            presentation_name, language_code = parse_speech_directory_name(speech_dir.name)
            
            # Determine style
            style = determine_style_from_presentation(presentation_name)
            
            # Migrate directory
            success = migrate_speech_directory(
                speech_dir, presentation_name, language_code, style, dry_run
            )
            
            if success:
                stats["successful"] += 1
                
                # Clean up old directory if requested and not dry run
                if cleanup and not dry_run:
                    try:
                        shutil.rmtree(speech_dir)
                        logger.info(f"✓ Cleaned up old directory: {speech_dir}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {speech_dir}: {e}")
            else:
                stats["failed"] += 1
                
        except Exception as e:
            logger.error(f"✗ Failed to process {speech_dir.name}: {e}")
            stats["failed"] += 1
    
    return stats


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate speech files from cache/speech to output structure"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without actually moving files"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true", 
        help="Remove old cache/speech directories after successful migration"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 80)
    logger.info("SPEECH FILES MIGRATION")
    logger.info("=" * 80)
    logger.info("Migrating speech files from cache/speech to output/[style]/generate structure")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be moved")
    
    if args.cleanup:
        logger.info("CLEANUP MODE - Old directories will be removed after migration")
    
    logger.info("=" * 80)
    
    # Perform migration
    stats = migrate_all_speech_files(dry_run=args.dry_run, cleanup=args.cleanup)
    
    # Print summary
    logger.info("=" * 80)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total directories processed: {stats['total']}")
    logger.info(f"Successfully migrated: {stats['successful']}")
    logger.info(f"Failed migrations: {stats['failed']}")
    
    if stats['total'] > 0:
        success_rate = (stats['successful'] / stats['total']) * 100
        logger.info(f"Success rate: {success_rate:.1f}%")
    
    if args.dry_run:
        logger.info("\nTo perform the actual migration, run without --dry-run")
    
    if stats['successful'] > 0 and not args.cleanup and not args.dry_run:
        logger.info("\nTo clean up old cache directories, run with --cleanup")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()