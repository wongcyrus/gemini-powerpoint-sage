#!/usr/bin/env python3
"""
Gemini PowerPoint Sage

Enhances PowerPoint presentations by generating speaker notes using a
Supervisor-Tool Multi-Agent System.
"""

import sys
from application import CLI, setup_logging


def main() -> int:
    """Main entry point."""
    # Setup logging
    setup_logging()
    
    # Run CLI
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
