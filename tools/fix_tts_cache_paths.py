#!/usr/bin/env python3
"""
Fix TTS cache metadata to point to new file locations after directory restructure.

This script updates the cache metadata to reflect the new speech file locations
in output/[style]/generate/ instead of cache/speech/.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_old_speech_path(old_path: str) -> Dict[str, str]:
    """
    Parse old speech file path to extract components.
    
    Args:
        old_path: Old path like "cache/speech/Module 4a_en_speech/slide_24_hash.mp3"
        
    Returns:
        Dictionary with parsed components
    """
    path_obj = Path(old_path)
    
    # Extract filename
    filename = path_obj.name
    
    # Extract directory name (presentation_language_speech)
    dir_name = path_obj.parent.name
    
    if not dir_name.endswith('_speech'):
        raise ValueError(f"Invalid speech directory name: {dir_name}")
    
    # Remove _speech suffix
    base_name = dir_name[:-8]
    
    # Find the last underscore to separate language code
    parts = base_name.rsplit('_', 1)
    if len(parts) != 2:
        raise ValueError(f"Cannot parse language from directory name: {dir_name}")
    
    presentation_name, language_code = parts
    
    return {
        "presentation_name": presentation_name,
        "language_code": language_code,
        "filename": filename,
        "original_path": old_path
    }


def determine_new_speech_path(parsed_info: Dict[str, str], style: str = "professional") -> str:
    """
    Determine the new speech file path based on the restructured directory.
    
    Args:
        parsed_info: Parsed information from old path
        style: Style name (defaults to professional)
        
    Returns:
        New file path
    """
    presentation_name = parsed_info["presentation_name"]
    language_code = parsed_info["language_code"]
    filename = parsed_info["filename"]
    
    # Create new directory structure
    if style.lower() == "professional":
        base_output_dir = Path("output") / "professional" / "generate"
    else:
        style_folder = style.replace(" ", "_").lower()
        base_output_dir = Path("output") / style_folder / "generate"
    
    # Create speech directory name - need to handle language code truncation
    # The migration script truncated language codes, so we need to match that
    if language_code == "en":
        lang_suffix = "e"
    elif language_code == "zh-CN":
        lang_suffix = "zh-C"
    elif language_code == "yue-HK":
        lang_suffix = "yue-H"
    else:
        lang_suffix = language_code
    
    speech_dir_name = f"{presentation_name}_{lang_suffix}_speech"
    new_path = base_output_dir / speech_dir_name / filename
    
    return str(new_path)


def fix_tts_cache_metadata(dry_run: bool = False) -> Dict[str, int]:
    """
    Fix TTS cache metadata to point to new file locations.
    
    Args:
        dry_run: If True, only show what would be changed
        
    Returns:
        Dictionary with fix statistics
    """
    cache_metadata_path = Path("cache/tts/cache_metadata.json")
    
    if not cache_metadata_path.exists():
        logger.error("TTS cache metadata file not found")
        return {"total": 0, "fixed": 0, "errors": 0}
    
    # Load existing metadata
    try:
        with open(cache_metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load cache metadata: {e}")
        return {"total": 0, "fixed": 0, "errors": 0}
    
    stats = {"total": len(metadata), "fixed": 0, "errors": 0, "skipped": 0}
    
    logger.info(f"Processing {stats['total']} cache entries")
    
    # Process each cache entry
    for cache_key, entry in metadata.items():
        try:
            old_file_path = entry.get("file_path", "")
            
            # Skip if not a cache/speech path
            if not old_file_path.startswith("cache/speech/"):
                stats["skipped"] += 1
                continue
            
            # Parse old path
            parsed_info = parse_old_speech_path(old_file_path)
            
            # Determine new path
            new_file_path = determine_new_speech_path(parsed_info)
            
            # Check if new file exists
            if not Path(new_file_path).exists():
                logger.warning(f"New file does not exist: {new_file_path}")
                stats["errors"] += 1
                continue
            
            if dry_run:
                logger.info(f"[DRY RUN] Would update: {old_file_path} -> {new_file_path}")
            else:
                # Update the entry
                entry["file_path"] = new_file_path
                if "tts_result" in entry and "file_path" in entry["tts_result"]:
                    entry["tts_result"]["file_path"] = new_file_path
                
                logger.debug(f"Updated cache entry: {cache_key}")
            
            stats["fixed"] += 1
            
        except Exception as e:
            logger.error(f"Error processing cache entry {cache_key}: {e}")
            stats["errors"] += 1
    
    # Save updated metadata
    if not dry_run and stats["fixed"] > 0:
        try:
            # Create backup
            backup_path = cache_metadata_path.with_suffix('.json.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Created backup: {backup_path}")
            
            # Save updated metadata
            with open(cache_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Updated cache metadata: {cache_metadata_path}")
            
        except Exception as e:
            logger.error(f"Failed to save updated metadata: {e}")
            stats["errors"] += 1
    
    return stats


def validate_cache_integrity() -> Dict[str, Any]:
    """
    Validate that cached files exist at their specified paths.
    
    Returns:
        Validation results
    """
    cache_metadata_path = Path("cache/tts/cache_metadata.json")
    
    if not cache_metadata_path.exists():
        return {"error": "Cache metadata file not found"}
    
    try:
        with open(cache_metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load metadata: {e}"}
    
    results = {
        "total_entries": len(metadata),
        "valid_files": 0,
        "missing_files": 0,
        "invalid_paths": 0,
        "missing_files_list": []
    }
    
    for cache_key, entry in metadata.items():
        try:
            file_path = entry.get("file_path", "")
            if not file_path:
                results["invalid_paths"] += 1
                continue
            
            if Path(file_path).exists():
                results["valid_files"] += 1
            else:
                results["missing_files"] += 1
                results["missing_files_list"].append(file_path)
                
        except Exception:
            results["invalid_paths"] += 1
    
    return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Fix TTS cache metadata after directory restructure"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate cache integrity without making changes"
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
    logger.info("TTS CACHE METADATA FIX")
    logger.info("=" * 80)
    
    if args.validate:
        logger.info("Validating cache integrity...")
        results = validate_cache_integrity()
        
        if "error" in results:
            logger.error(f"Validation failed: {results['error']}")
            return 1
        
        logger.info("=" * 80)
        logger.info("CACHE VALIDATION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Total entries: {results['total_entries']}")
        logger.info(f"Valid files: {results['valid_files']}")
        logger.info(f"Missing files: {results['missing_files']}")
        logger.info(f"Invalid paths: {results['invalid_paths']}")
        
        if results['missing_files'] > 0:
            logger.warning(f"Found {results['missing_files']} missing files")
            if args.verbose:
                for missing_file in results['missing_files_list'][:10]:  # Show first 10
                    logger.warning(f"  Missing: {missing_file}")
                if len(results['missing_files_list']) > 10:
                    logger.warning(f"  ... and {len(results['missing_files_list']) - 10} more")
        
        integrity_rate = (results['valid_files'] / results['total_entries']) * 100 if results['total_entries'] > 0 else 0
        logger.info(f"Cache integrity: {integrity_rate:.1f}%")
        
        return 0 if results['missing_files'] == 0 else 1
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    logger.info("Fixing TTS cache metadata...")
    
    # Fix cache metadata
    stats = fix_tts_cache_metadata(dry_run=args.dry_run)
    
    # Print summary
    logger.info("=" * 80)
    logger.info("FIX SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total entries processed: {stats['total']}")
    logger.info(f"Entries fixed: {stats['fixed']}")
    logger.info(f"Entries skipped: {stats['skipped']}")
    logger.info(f"Errors: {stats['errors']}")
    
    if stats['total'] > 0:
        success_rate = (stats['fixed'] / stats['total']) * 100
        logger.info(f"Success rate: {success_rate:.1f}%")
    
    if args.dry_run and stats['fixed'] > 0:
        logger.info("\nTo apply the fixes, run without --dry-run")
    
    logger.info("=" * 80)
    
    return 0 if stats['errors'] == 0 else 1


if __name__ == "__main__":
    exit(main())