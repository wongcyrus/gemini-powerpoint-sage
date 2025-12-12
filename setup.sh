#!/bin/bash

# Setup script for Gemini Powerpoint Sage (Linux/macOS)

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================"
echo "Gemini Powerpoint Sage - Setup"
echo "========================================"
echo ""

# Check if Python is available
PYTHON_CMD=""
for cmd in /opt/conda/bin/python3.12 python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v $cmd &> /dev/null; then
        PYTHON_CMD=$cmd
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: python3 is not installed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo "Found Python: $PYTHON_VERSION"
echo ""

# Create virtual environment if it doesn't exist
if [ -d ".venv" ]; then
    echo "Virtual environment already exists at .venv"
    # Automatic recreation if we are in a CI/scripted environment or user passed flag could be added
    # For now, we keep interactive but allow "force" via arg if we wanted, 
    # but simpler to just check if we need to recreate. 
    # Since we changed python version logic, let's assume if the user runs setup, they might want to ensure it matches.
    # However, to avoid breaking existing interactive flows, we'll keep the prompt logic but rely on user action.
    # For this specific interaction, I will delete .venv externally.
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf .venv
    else
        echo "Using existing virtual environment."
    fi
fi

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment using $PYTHON_CMD..."
    $PYTHON_CMD -m venv .venv
    echo "Virtual environment created at .venv"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo ""
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo ""
echo "To use the tool:"
echo "  1. Run: source .venv/bin/activate"
echo "  2. Choose a processing mode:"
echo "     • All styles:    ./run.sh --styles"
echo "     • Single style:  ./run.sh --style-config cyberpunk"
echo "     • Single file:   ./run.sh --pptx file.pptx --language en --style Professional"
echo ""
echo "Or simply use ./run.sh (defaults to --styles) which will auto-activate the venv"
echo ""
