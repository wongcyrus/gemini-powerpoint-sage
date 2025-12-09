# Run Scripts Usage Guide

## Overview

The run scripts (`run.sh` for Linux/Mac and `run.ps1` for Windows) provide convenient wrappers for executing the Gemini Powerpoint Sage with automatic virtual environment activation.

## Updated Features

Both scripts now support **four execution modes**:

1. **Single File Mode** - Process a specific PPTX file
2. **Folder Mode** - Process all PPTX files in a folder
3. **Config File Mode** - Use a YAML configuration file (NEW!)
4. **Refine Mode** - Refine existing progress files for TTS

## Usage

### Linux/Mac (run.sh)

```bash
# Single file mode
./run.sh --pptx <path_to_pptx> [--pdf <path_to_pdf>] [other flags]

# Folder mode
./run.sh --folder <path_to_folder> [--language <locale>]

# Config file mode (NEW!)
./run.sh --config <config_file.yaml>

# Refine mode
./run.sh --refine <progress_file.json>
```

### Windows (run.ps1)

```powershell
# Single file mode
./run.ps1 --pptx <path_to_pptx> [--pdf <path_to_pdf>] [other flags]

# Folder mode
./run.ps1 --folder <path_to_folder> [--language <locale>]

# Config file mode (NEW!)
./run.ps1 --config <config_file.yaml>

# Refine mode
./run.ps1 --refine <progress_file.json>
```

## Examples

### Using Config Files (Recommended for Styled Presentations)

```bash
# Use Gundam style configuration
./run.sh --config config.gundam.yaml

# Use Cyberpunk style configuration
./run.sh --config config.cyberpunk.yaml

# Use custom configuration
./run.sh --config my-custom-config.yaml
```

**Why use config files?**
- Easier to manage complex style definitions
- Reusable configurations for consistent styling
- Better for multi-line style descriptions
- Cleaner command line

### Single File Mode

```bash
# Basic usage (auto-detects PDF)
./run.sh --pptx tests/sample_data/cloudtech.pptm

# With explicit PDF
./run.sh --pptx presentation.pptx --pdf presentation.pdf

# With style
./run.sh --pptx presentation.pptx --style "Minimalist"

# With language
./run.sh --pptx presentation.pptx --language zh-CN

# Skip visuals (notes only)
./run.sh --pptx presentation.pptx --skip-visuals

# Generate videos
./run.sh --pptx presentation.pptx --generate-videos
```

### Folder Mode

```bash
# Process all PPTX files in a folder
./run.sh --folder ./presentations

# With language
./run.sh --folder ./presentations --language yue-HK

# With multiple languages
./run.sh --folder ./presentations --language "en,zh-CN,yue-HK"
```

### Refine Mode

```bash
# Refine for TTS (removes markdown, simplifies text)
./run.sh --refine cloudtech_en_progress.json
```

## Config File Mode Details

### What Gets Loaded from Config Files

When you use `--config`, the following settings are loaded:

- `pptx` - Input PowerPoint file path
- `pdf` - Input PDF file path
- `region` - Google Cloud region
- `language` - Target language(s)
- `style` - Visual and speaker styles (can be string or dict)
  - `visual_style` - Style for slide design
  - `speaker_style` - Style for speaker notes
- `skip_visuals` - Whether to skip visual generation
- `generate_videos` - Whether to generate videos
- `retry_errors` - Whether to retry failed slides

### Command-Line Override

Command-line arguments **always override** config file settings:

```bash
# Config says language: "en", but this overrides to Chinese
./run.sh --config config.gundam.yaml --language zh-CN

# Config has skip_visuals: false, but this skips them
./run.sh --config config.gundam.yaml --skip-visuals
```

### Example Config File

```yaml
# config.example.yaml
pptx: "tests/sample_data/cloudtech.pptm"
pdf: "tests/sample_data/cloudtech.pdf"
region: "global"
language: "en"

style:
  visual_style: |
    Modern minimalist design with clean lines.
    Pastel color palette (soft blues, grays, whites).
    Sans-serif typography (Helvetica, Arial).
    Generous white space for breathing room.
    
  speaker_style: |
    Professional and approachable tone.
    Clear, concise explanations.
    Uses analogies to simplify complex topics.
    Conversational but authoritative.

skip_visuals: false
generate_videos: false
```

## Script Features

### Automatic Virtual Environment

Both scripts automatically activate the `.venv` virtual environment if it exists:

```bash
# Linux/Mac
source .venv/bin/activate

# Windows
.\.venv\Scripts\Activate.ps1
```

If the virtual environment doesn't exist, they warn you but continue with system Python.

### Environment Variables

Scripts load environment variables from `.env` file automatically via `python-dotenv`.

You can still override them in the script if needed:

```bash
# In run.sh
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

```powershell
# In run.ps1
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"
$env:GOOGLE_CLOUD_LOCATION = "us-central1"
```

### Error Handling

Both scripts:
- Check for required arguments
- Validate mode selection (can't mix --pptx with --folder)
- Return proper exit codes
- Display success/failure messages

## Validation Rules

### Mode Exclusivity

You can only use **one mode** at a time:

```bash
# ❌ INVALID - Cannot mix modes
./run.sh --pptx file.pptx --config config.yaml

# ✅ VALID - One mode at a time
./run.sh --config config.yaml
./run.sh --pptx file.pptx
```

### Required Arguments

Each mode has its own requirements:

- **Single File Mode**: Requires `--pptx` (PDF is optional)
- **Folder Mode**: Requires `--folder`
- **Config Mode**: Requires `--config`
- **Refine Mode**: Requires `--refine`

## Troubleshooting

### "Virtual environment not found"

Run the setup script first:

```bash
./setup.sh        # Linux/Mac
./setup.ps1       # Windows
```

### "Python interpreter not found"

Install Python 3.8+ and ensure it's in your PATH.

### "Error loading configuration file"

Check that:
- The config file exists
- The YAML syntax is valid
- Required fields (pptx, pdf) are present

### Permission Denied (Linux/Mac)

Make the script executable:

```bash
chmod +x run.sh
```

## Direct Python Execution

You can always bypass the run scripts and call Python directly:

```bash
# Activate venv manually
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\Activate   # Windows

# Run directly
python main.py --config config.gundam.yaml
python main.py --pptx file.pptx --pdf file.pdf
```

This gives you full control and is useful for debugging.

## Summary

The updated run scripts now support config file mode, making it much easier to work with complex style configurations. Use config files for styled presentations and direct arguments for quick one-off runs.

**Quick Reference:**

```bash
# Styled presentation (recommended)
./run.sh --config config.gundam.yaml

# Quick single file
./run.sh --pptx presentation.pptx

# Batch processing
./run.sh --folder ./presentations

# TTS refinement
./run.sh --refine progress.json
```
