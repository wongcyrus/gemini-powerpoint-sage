#!/usr/bin/env python3
"""
Run all style configurations on a presentation.

Usage:
    python run_all_styles.py <pptx_file> <pdf_file> [language]

Examples:
    python run_all_styles.py presentation.pptx presentation.pdf
    python run_all_styles.py presentation.pptx presentation.pdf zh-CN
    python run_all_styles.py presentation.pptx presentation.pdf "en,zh-CN,ja"
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Tuple
import logging
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


def print_banner():
    """Print the script banner."""
    print(f"{Colors.BLUE}╔════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.BLUE}║          Running All Style Configurations                 ║{Colors.NC}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════════════════════════╝{Colors.NC}")
    print()


def print_separator():
    """Print a separator line."""
    print(f"{Colors.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")


def find_style_configs() -> List[Path]:
    """Find all style configuration files."""
    styles_dir = Path("styles")
    if not styles_dir.exists():
        return []
    
    configs = list(styles_dir.glob("config.*.yaml"))
    return sorted(configs)


async def process_style(
    config_path: Path,
    language: str
) -> Tuple[str, bool]:
    """
    Process a single style configuration.
    
    Returns:
        Tuple of (style_name, success)
    """
    style_name = config_path.stem.replace("config.", "")
    
    print_separator()
    print(f"{Colors.GREEN}Processing Style: {Colors.YELLOW}{style_name}{Colors.NC}")
    print_separator()
    print()
    
    # Import here to avoid circular imports
    from application.cli import CLI
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Build command-line arguments
    argv = [
        "--config", str(config_path),
        "--language", language
    ]
    
    try:
        cli = CLI()
        args = cli.parser.parse_args(argv)
        
        # Load config file
        cli._load_config_file(args)
        
        # Validate input
        if not args.pptx and not args.folder:
            print(f"{Colors.RED}Error: Config must specify pptx or folder{Colors.NC}")
            return style_name, False
        
        if args.pptx and args.folder:
            print(f"{Colors.RED}Error: Config cannot specify both pptx and folder{Colors.NC}")
            return style_name, False
        
        # Setup environment
        cli._setup_environment(args)
        
        # Handle batch or single mode
        if args.folder:
            await cli._handle_batch(args)
        else:
            await cli._handle_single(args)
        
        print()
        print(f"{Colors.GREEN}✓ Successfully processed: {style_name}{Colors.NC}")
        return style_name, True
        
    except Exception as e:
        print()
        print(f"{Colors.RED}✗ Failed to process: {style_name}{Colors.NC}")
        print(f"{Colors.RED}Error: {e}{Colors.NC}")
        import traceback
        traceback.print_exc()
        return style_name, False


def activate_venv():
    """Activate virtual environment if it exists."""
    script_dir = Path(__file__).parent
    venv_dir = script_dir / ".venv"
    
    if venv_dir.exists():
        print("Activating virtual environment...")
        # Check if we're already in a venv
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("Already in virtual environment")
            return
        
        # Activate venv by modifying sys.path
        if sys.platform == "win32":
            activate_script = venv_dir / "Scripts" / "activate_this.py"
            site_packages = venv_dir / "Lib" / "site-packages"
        else:
            activate_script = venv_dir / "bin" / "activate_this.py"
            site_packages = venv_dir / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        
        # Add site-packages to path
        if site_packages.exists():
            sys.path.insert(0, str(site_packages))
    else:
        print("Warning: Virtual environment not found. Run ./setup.sh or .\\setup.ps1 first.")
        print("Continuing with system Python...")


async def main():
    """Main entry point."""
    # Activate venv first
    activate_venv()
    
    # Parse arguments - language is optional
    language = sys.argv[1] if len(sys.argv) > 1 else "en"
    
    # Find style configs
    style_configs = find_style_configs()
    
    if not style_configs:
        print(f"{Colors.RED}Error: No style configuration files found in styles/{Colors.NC}")
        sys.exit(1)
    
    # Display banner
    print_banner()
    print(f"{Colors.GREEN}Language: {Colors.YELLOW}{language}{Colors.NC}")
    print()
    print(f"{Colors.GREEN}Found {len(style_configs)} style configuration(s):{Colors.NC}")
    for config in style_configs:
        style_name = config.stem.replace("config.", "")
        print(f"  - {Colors.YELLOW}{style_name}{Colors.NC}")
    print()
    print(f"{Colors.YELLOW}Note: PPTX and PDF paths are read from each config file{Colors.NC}")
    print()
    
    # Process each style
    results = []
    for config in style_configs:
        style_name, success = await process_style(config, language)
        results.append((style_name, success))
        print()
    
    # Display summary
    successful = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    
    print(f"{Colors.BLUE}╔════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.BLUE}║                    Processing Summary                      ║{Colors.NC}")
    print(f"{Colors.BLUE}╚════════════════════════════════════════════════════════════╝{Colors.NC}")
    print()
    print(f"{Colors.GREEN}Successful: {successful}{Colors.NC}")
    print(f"{Colors.RED}Failed: {failed}{Colors.NC}")
    print()
    
    if failed > 0:
        print(f"{Colors.RED}Failed styles:{Colors.NC}")
        for style_name, success in results:
            if not success:
                print(f"  - {Colors.RED}{style_name}{Colors.NC}")
        print()
        sys.exit(1)
    else:
        print(f"{Colors.GREEN}🎉 All styles processed successfully!{Colors.NC}")
        print()
        print(f"{Colors.YELLOW}Output locations:{Colors.NC}")
        for style_name, _ in results:
            print(f"  - {style_name}/generate/")
        print()


if __name__ == "__main__":
    asyncio.run(main())
