#!/bin/bash

# Haio Drive Client Build Script
echo "Building Haio Drive Client..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if rclone is available (warn if not found)
if ! command -v rclone >/dev/null 2>&1; then
    echo "Warning: rclone not found in PATH"
    echo "The built application will require rclone to be installed separately"
    echo "Run ./setup_linux.sh to install dependencies"
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/
rm -rf dist/

# Create desktop entry directory if it doesn't exist
mkdir -p ~/.local/share/applications

# Build the application using spec file
echo "Building executable with PyInstaller..."
pyinstaller s3_mounter.spec

# Check if build was successful
if [ $? -eq 0 ] && [ -f "dist/HaioDriveClient" ]; then
    echo "✓ Build successful!"
    echo "Executable created at: dist/HaioDriveClient"
    
    # Make executable
    chmod +x dist/HaioDriveClient
    
    # Show file size
    ls -lh dist/HaioDriveClient
    
    # Create desktop entry
    cat > ~/.local/share/applications/haio-drive-client.desktop << EOF
[Desktop Entry]
Name=Haio Drive Client
Comment=Connect and mount Haio cloud storage buckets
Exec=$(pwd)/dist/HaioDriveClient
Icon=drive-harddisk
Type=Application
Categories=Utility;FileManager;Network;
StartupNotify=true
EOF
    
    echo "✓ Desktop entry created"
    echo ""
    echo "Installation complete!"
    echo "You can now:"
    echo "1. Run the executable: ./dist/HaioDriveClient"
    echo "2. Find it in your applications menu as 'Haio Drive Client'"
    echo ""
    echo "Note: The target system must have rclone and FUSE installed"
    echo "Run ./setup_linux.sh on the target system to install dependencies"
else
    echo "✗ Build failed!"
    exit 1
fi
