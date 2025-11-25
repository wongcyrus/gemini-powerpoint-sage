#!/bin/bash

# Helper script to run the Gemini Powerpoint Sage

# Ensure we are in the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Check arguments
if [ "$#" -lt 4 ]; then
    echo "Usage: ./run.sh --pptx <path_to_pptx> --pdf <path_to_pdf>"
    echo "Example: ./run.sh --pptx ../data/deck.pptx --pdf ../data/deck.pdf"
    exit 1
fi

# Set Google Cloud Environment Variables
# You may need to adjust these or set them in your shell before running
export GOOGLE_CLOUD_PROJECT="langbridge-presenter"
export GOOGLE_CLOUD_LOCATION="global"
export GOOGLE_GENAI_USE_VERTEXAI="True"

# Default region
export GOOGLE_CLOUD_LOCATION="global"

echo "Starting Gemini Powerpoint Sage..."
echo "Project: $GOOGLE_CLOUD_PROJECT"

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
