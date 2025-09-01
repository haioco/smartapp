#!/bin/bash
# Haio Drive Client Launcher

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Starting Haio Drive Client..."

# Check if rclone is installed
if ! command -v rclone &> /dev/null; then
    echo "Warning: rclone is not installed. Mounting functionality will not work."
    echo "To install rclone: sudo apt install rclone"
    echo ""
fi

# Check if executable exists
if [ -f "$DIR/dist/HaioDriveClient" ]; then
    echo "Launching Haio Drive Client..."
    "$DIR/dist/HaioDriveClient"
elif [ -f "$DIR/main.py" ]; then
    echo "Running from source..."
    if [ -f "$DIR/venv/bin/python" ]; then
        "$DIR/venv/bin/python" "$DIR/main.py"
    else
        python3 "$DIR/main.py"
    fi
else
    echo "Error: Haio Drive Client not found!"
    echo "Please build the application first by running: ./build.sh"
    exit 1
fi
