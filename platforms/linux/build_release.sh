#!/bin/bash

# Haio Smart Solutions - Build Release Script
# Version: 1.3.0

echo "Building Haio Smart Solutions v1.3.0..."
echo "==========================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -f *.spec~

# Build the application (rclone will be downloaded automatically by spec file)
echo "Building application with PyInstaller..."
pyinstaller s3_mounter.spec

# Check if build was successful
if [ -f "dist/HaioSmartApp" ]; then
    echo "SUCCESS: Build successful!"
    echo "Executable location: dist/HaioSmartApp"
    echo ""
    echo "Release v1.3.0 Features:"
    echo "  - Bundled rclone and dependencies"
    echo "  - Enhanced login dialog with window dragging"
    echo "  - Professional UI/UX improvements"
    echo "  - Application icon support"
    echo "  - Circular logo masking"
    echo "  - Improved authentication flow"
    echo "  - Rebranded to 'Haio Smart Solutions'"
    echo ""
    echo "To distribute:"
    echo "  1. Copy dist/HaioSmartApp to target systems"
    echo "  2. Dependencies are now bundled automatically"
    echo "  3. On Linux: FUSE will be checked at runtime"
    
    # Create release notes
    echo ""
    echo "Creating release notes..."
    cat > dist/RELEASE_NOTES.txt << EOF
Haio Smart Solutions Client v1.3.0
==================================

What's New in v1.3.0:

Bundled Dependencies:
- Bundled rclone binary - no separate download needed
- WinFsp installer included for Windows
- Auto-installation of missing dependencies
- Fully self-contained application

Enhanced User Experience:
- Professional login dialog with draggable window
- Improved form layouts and component sizing
- Better error handling and user feedback
- Loading states during authentication

Visual Improvements:
- Rebranded to "Haio Smart Solutions"
- Application icon for taskbar and window
- Circular logo masking for better integration
- Professional styling and color schemes
- Enhanced header design

Bug Fixes:
- Fixed login window dragging functionality
- Resolved label visibility issues
- Better PyQt6 compatibility
- Removed CSS warnings
- Fixed Windows build encoding issues

System Requirements:
- Linux: FUSE support (auto-installed if missing)
- Windows: WinFsp (auto-installed from bundled installer)
- All dependencies bundled with application

Installation:
1. Download and run HaioSmartApp
2. Accept dependency installation prompts if needed
3. Login with your Haio credentials
4. Mount and access your cloud storage

For support: contact@haio.ir
EOF
    
    echo "Release notes created: dist/RELEASE_NOTES.txt"
    
else
    echo "ERROR: Build failed! Check the output above for errors."
    exit 1
fi

echo ""
echo "Release v1.3.0 build completed successfully!"