#!/bin/bash

# Helper script to run the Gemini Powerpoint Sage

# Ensure we are in the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Basic presence check for --pptx or --folder
if ! printf '%s\n' "$@" | grep -qE -- '--(pptx|folder|refine)'; then
    echo "Usage: ./run.sh --pptx <path_to_pptx> [--pdf <path_to_pdf>] [other flags]" >&2
    echo "   or: ./run.sh --folder <path_to_folder> [--language <locale>]" >&2
    echo "If --pdf omitted, main.py auto-detects a PDF with the same basename in the PPTX folder." >&2
    echo "Example: ./run.sh --pptx ../data/deck.pptx" >&2
    echo "Example: ./run.sh --folder ../data --language zh-CN" >&2
    exit 1
fi


# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Warning: Virtual environment not found. Run ./setup.sh first."
    echo "Continuing with system Python..."
fi

# Note: Environment variables are loaded from .env file by main.py using python-dotenv
# You can still override them here if needed:
# export GOOGLE_CLOUD_PROJECT="your-project-id"
# export GOOGLE_CLOUD_LOCATION="us-central1"

echo "Starting Gemini Powerpoint Sage..."
if [ -n "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "Project: $GOOGLE_CLOUD_PROJECT"
else
    echo "Project: (will be loaded from .env file)"
fi

# Run the python script
# Arguments are passed directly, so if user provides --region, python argparse handles it.
python3 main.py "$@"

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "Success!"
else
    echo "Failed with error code $EXIT_CODE"
fi
exit $EXIT_CODE
