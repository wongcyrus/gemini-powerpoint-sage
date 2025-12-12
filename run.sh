#!/bin/bash

# Helper script to run the Gemini Powerpoint Sage
# Updated for the new three-mode system

# Ensure we are in the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Show usage if no arguments or help requested
if [ $# -eq 0 ] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Gemini PowerPoint Sage - Three Processing Modes" >&2
    echo "" >&2
    echo "🌟 All Styles Processing (recommended):" >&2
    echo "  ./run.sh --styles" >&2
    echo "  ./run.sh                    # defaults to --styles" >&2
    echo "" >&2
    echo "🎨 Single Style Processing:" >&2
    echo "  ./run.sh --style-config cyberpunk" >&2
    echo "  ./run.sh --style-config professional" >&2
    echo "  ./run.sh --style-config gundam" >&2
    echo "" >&2
    echo "📄 Single File Processing:" >&2
    echo "  ./run.sh --pptx file.pptx --language en --style Professional" >&2
    echo "  ./run.sh --pptx file.pptx --language 'en,zh-CN' --style Cyberpunk" >&2
    echo "" >&2
    echo "🔧 Other Options:" >&2
    echo "  ./run.sh --refine progress.json" >&2
    echo "" >&2
    echo "ℹ️  All configuration is now handled through YAML files in styles/ directory" >&2
    echo "   Use --styles or --style-config for organized processing" >&2
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

# If no arguments provided, default to --styles
if [ $# -eq 0 ]; then
    echo "No arguments provided, defaulting to --styles mode"
    set -- --styles
fi

# Run the python script
python3 main.py "$@"

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "Success!"
else
    echo "Failed with error code $EXIT_CODE"
fi
exit $EXIT_CODE
