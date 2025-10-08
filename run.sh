#!/bin/bash
# Haio Smart Storage App Launcher for Linux
# This script runs the application with the correct Python environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists in parent directory
VENV_PATH="$SCRIPT_DIR/../.venv/bin/python"
if [ -f "$VENV_PATH" ]; then
    echo "Using virtual environment Python..."
    "$VENV_PATH" -m src.main
else
    # Fall back to system Python
    echo "Using system Python..."
    python3 -m src.main
fi
