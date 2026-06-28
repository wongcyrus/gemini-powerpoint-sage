#!/usr/bin/env python3
"""Usage examples for the YAML-first Gemini PowerPoint Sage system."""

import asyncio
import logging
from application.unified_processor import UnifiedProcessor
from application.input_scanner import InputScanner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_single_style():
    """Example: Process all files with one specific style configuration."""
    processor = UnifiedProcessor()
    
    try:
        # Process using cyberpunk style configuration
        results = await processor.process_single_style("cyberpunk")
        logger.info(f"Single style processing results: {results}")
        
        # Can also use full path to config file
        # results = await processor.process_single_style("/path/to/custom-config.yaml")
        
    except Exception as e:
        logger.error(f"Error processing single style: {e}")


async def example_all_styles():
    """Example: Process all files with all available style configurations."""
    processor = UnifiedProcessor()
    
    try:
        results = await processor.process_styles_directory()
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("All Styles Processing Summary:")
        for style_name, style_results in results.items():
            total_files = len(style_results)
            logger.info(f"  {style_name}: {total_files} files processed")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error processing all styles: {e}")


async def example_direct_config():
    """Example: Process one explicit YAML config file."""
    processor = UnifiedProcessor()

    try:
        results = await processor.process_config("styles/config.professional.yaml")
        logger.info(f"Direct config processing results: {results}")
    except Exception as e:
        logger.error(f"Error processing config file: {e}")


def example_input_scanning():
    """Example: Scan for available input files and configurations."""
    scanner = InputScanner(".")
    
    # Scan all sources
    all_sources = scanner.scan_all()
    
    logger.info("Available input sources:")
    for source_type, file_sets in all_sources.items():
        logger.info(f"\n{source_type.upper()}:")
        for file_set in file_sets:
            logger.info(f"  - {file_set.base_name}")
            if file_set.style:
                logger.info(f"    Style: {file_set.style}")
            if file_set.category:
                logger.info(f"    Category: {file_set.category}")
            logger.info(f"    PPTX: {file_set.pptx_path}")
            logger.info(f"    PDF: {file_set.pdf_path}")
    
    # Show available style configurations
    logger.info("\nAvailable Style Configurations:")
    from pathlib import Path
    styles_dir = Path("styles")
    if styles_dir.exists():
        config_files = list(styles_dir.glob("config.*.yaml"))
        for config_file in config_files:
            style_name = config_file.stem.replace("config.", "")
            logger.info(f"  - {style_name}: {config_file}")


def example_cli_commands():
    """Example: Show equivalent CLI commands for each YAML mode."""
    logger.info("CLI Command Examples:")

    logger.info("\n🧩 DIRECT CONFIG PROCESSING:")
    logger.info("  python main.py --config /path/to/config.yaml")

    logger.info("\n🎨 SINGLE STYLE PROCESSING:")
    logger.info("  python main.py --style-config cyberpunk")
    logger.info("  python main.py --style-config professional")
    logger.info("  python main.py --style-config gundam")
    
    logger.info("\n🌟 ALL STYLES PROCESSING:")
    logger.info("  python main.py --styles")
    logger.info("  python main.py  # defaults to --styles")


def example_use_cases():
    """Example: Show when to use each processing mode."""
    logger.info("Use Case Examples:")
    
    logger.info("\n🔧 DEVELOPMENT & TESTING:")
    logger.info("  # Use one explicit test config")
    logger.info("  python main.py --config configs/test-run.yaml")
    logger.info("")
    logger.info("  # Test specific style configuration")
    logger.info("  python main.py --style-config cyberpunk")
    
    logger.info("\n🏭 PRODUCTION & BATCH:")
    logger.info("  # Process all files with all styles")
    logger.info("  python main.py --styles")
    logger.info("  ")
    logger.info("  # Process all files with client-specific style")
    logger.info("  python main.py --style-config professional")
    
    logger.info("\n👥 TEAM WORKFLOW:")
    logger.info("  # Designer tests their style")
    logger.info("  python main.py --style-config gundam")
    logger.info("  ")
    logger.info("  # Content team processes everything")
    logger.info("  python main.py --styles")
    logger.info("  ")
    logger.info("  # QA validates specific output")
    logger.info("  python main.py --style-config professional")


async def main():
    """Run all examples."""
    logger.info("=== Gemini PowerPoint Sage - YAML-First Usage Examples ===\n")
    
    # Example 1: Input scanning
    logger.info("1. Input Scanning & Configuration Discovery:")
    example_input_scanning()
    
    # Example 2: CLI commands
    logger.info("\n2. CLI Command Examples:")
    example_cli_commands()
    
    # Example 3: Use cases
    logger.info("\n3. Use Case Examples:")
    example_use_cases()
    
    # Example 4: Direct config processing
    logger.info("\n4. Direct Config Processing Example:")
    await example_direct_config()

    # Example 5: Single style processing
    logger.info("\n5. Single Style Processing Example:")
    await example_single_style()
    
    # Example 6: All styles processing
    logger.info("\n6. All Styles Processing Example:")
    await example_all_styles()
    
    logger.info("\n🎉 Examples complete!")
    logger.info("\nQuick reference:")
    logger.info("  🧩 One config:   python main.py --config configs/run.yaml")
    logger.info("  🎨 Single style: python main.py --style-config cyberpunk")
    logger.info("  🌟 All styles:   python main.py --styles")


if __name__ == "__main__":
    asyncio.run(main())