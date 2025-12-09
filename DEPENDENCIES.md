# Dependencies Documentation

## Overview

This document lists all dependencies for the Gemini PowerPoint Sage project, organized by category.

## Production Dependencies

### Core Google AI Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `google-adk` | >=0.1.0 | Google Agent Development Kit - Core framework for building AI agents |
| `google-genai` | >=0.1.0 | Google Generative AI SDK - Access to Gemini models |

### Presentation and Document Processing

| Package | Version | Purpose |
|---------|---------|---------|
| `python-pptx` | >=0.6.21 | Create and modify PowerPoint presentations |
| `pymupdf` | >=1.23.0 | PDF processing and rendering (PyMuPDF/fitz) |
| `Pillow` | >=10.0.0 | Image processing and manipulation |

### Configuration and Environment

| Package | Version | Purpose |
|---------|---------|---------|
| `python-dotenv` | >=1.0.0 | Load environment variables from .env files |
| `pyyaml` | >=6.0 | YAML configuration file parsing |

### MCP Server (Optional)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastmcp` | >=0.1.0 | FastMCP framework for MCP server implementation |
| `pydantic` | >=2.0.0 | Data validation and settings management |

### Type Hints and Validation

| Package | Version | Purpose |
|---------|---------|---------|
| `typing-extensions` | >=4.8.0 | Backported type hints for older Python versions |

## Development Dependencies

### Testing Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.4.0 | Testing framework |
| `pytest-asyncio` | >=0.21.0 | Async test support for pytest |
| `pytest-cov` | >=4.1.0 | Code coverage reporting |
| `pytest-mock` | >=3.11.1 | Mocking support for pytest |

### Code Quality

| Package | Version | Purpose |
|---------|---------|---------|
| `black` | >=23.7.0 | Code formatter |
| `flake8` | >=6.1.0 | Linting and style checking |
| `mypy` | >=1.5.0 | Static type checking |
| `isort` | >=5.12.0 | Import sorting |
| `ruff` | >=0.1.0 | Fast Python linter |

### Type Stubs

| Package | Version | Purpose |
|---------|---------|---------|
| `types-Pillow` | >=10.0.0 | Type stubs for Pillow |
| `types-PyYAML` | >=6.0.0 | Type stubs for PyYAML |

### Documentation

| Package | Version | Purpose |
|---------|---------|---------|
| `sphinx` | >=7.1.0 | Documentation generator |
| `sphinx-rtd-theme` | >=1.3.0 | Read the Docs theme for Sphinx |

## Installation

### Production Environment

```bash
pip install -r requirements.txt
```

### Development Environment

```bash
pip install -r requirements-dev.txt
```

This will install both production and development dependencies.

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
```

## Optional Dependencies

### Video Generation (Veo MCP Server)

The video generation feature requires additional setup:

1. Install MCP dependencies (included in requirements.txt):
   - `fastmcp`
   - `pydantic`

2. Set environment variable:
   ```bash
   export USE_MCP_VIDEO_AGENT=1
   ```

3. Configure MCP server in `.kiro/settings/mcp.json` (if using Kiro IDE)

## Python Version

- **Minimum**: Python 3.10
- **Recommended**: Python 3.11 or 3.12
- **Tested**: Python 3.12.3

## System Dependencies

Some packages may require system-level dependencies:

### PyMuPDF (pymupdf)

- **Linux**: `sudo apt-get install libmupdf-dev`
- **macOS**: Usually works out of the box
- **Windows**: Usually works out of the box

### Pillow

- **Linux**: `sudo apt-get install libjpeg-dev zlib1g-dev`
- **macOS**: Usually works out of the box
- **Windows**: Usually works out of the box

## Dependency Updates

To update dependencies:

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade google-adk

# Check for outdated packages
pip list --outdated
```

## Security

To check for security vulnerabilities:

```bash
# Install safety
pip install safety

# Check dependencies
safety check -r requirements.txt
```

## Troubleshooting

### Import Errors

If you encounter import errors:

1. Verify virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Check Python version: `python --version`

### Version Conflicts

If you encounter version conflicts:

1. Create a fresh virtual environment
2. Install dependencies in order:
   ```bash
   pip install google-adk google-genai
   pip install -r requirements.txt
   ```

### PyYAML Not Found

If YAML config loading fails:

```bash
pip install pyyaml
```

## License Compatibility

All dependencies use permissive licenses compatible with this project:

- Apache 2.0: google-adk, google-genai
- MIT: python-pptx, python-dotenv, pyyaml, pytest, black, etc.
- AGPL: pymupdf (note: commercial use may require license)
- PIL License: Pillow

## Contributing

When adding new dependencies:

1. Add to `requirements.txt` (production) or `requirements-dev.txt` (development)
2. Include version constraint (>=, ==, or ~=)
3. Add comment explaining purpose
4. Update this documentation
5. Test installation in clean virtual environment
