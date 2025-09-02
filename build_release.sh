#!/bin/bash

# Haio Smart Solutions - Build Release Script
# Version: 1.2.1

echo "🚀 Building Haio Smart Solutions v1.2.1..."
echo "==========================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install/update dependencies
echo "📋 Installing dependencies..."
pip install -r requirements.txt

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -f *.spec~

# Build the application
echo "🔨 Building application with PyInstaller..."
pyinstaller s3_mounter.spec

# Check if build was successful
if [ -f "dist/HaioSmartApp" ]; then
    echo "✅ Build successful!"
    echo "📁 Executable location: dist/HaioSmartApp"
    echo ""
    echo "🎯 Release v1.2.1 Features:"
    echo "  - Enhanced login dialog with window dragging"
    echo "  - Professional UI/UX improvements"
    echo "  - Application icon support"
    echo "  - Circular logo masking"
    echo "  - Improved authentication flow"
    echo "  - Rebranded to 'Haio Smart Solutions'"
    echo ""
    echo "📋 To distribute:"
    echo "  1. Copy dist/HaioSmartApp to target systems"
    echo "  2. Ensure rclone is installed and in PATH"
    echo "  3. On Linux: ensure FUSE is installed"
    echo "  4. On Windows: ensure WinFsp is installed"
    
    # Create a simple installer info
    echo ""
    echo "📄 Creating release notes..."
    cat > dist/RELEASE_NOTES.txt << EOF
Haio Smart Solutions Client v1.2.1
==================================

🚀 What's New in v1.2.1:

✨ Enhanced User Experience:
- Professional login dialog with draggable window
- Improved form layouts and component sizing
- Better error handling and user feedback
- Loading states during authentication

🎨 Visual Improvements:
- Rebranded to "Haio Smart Solutions"
- Application icon for taskbar and window
- Circular logo masking for better integration
- Professional styling and color schemes
- Enhanced header design

🐛 Bug Fixes:
- Fixed login window dragging functionality
- Resolved label visibility issues
- Better PyQt6 compatibility
- Removed CSS warnings

📋 System Requirements:
- Linux: FUSE support (sudo apt-get install fuse)
- Windows: WinFsp (https://github.com/billziss-gh/winfsp/releases)
- rclone binary in PATH or same directory

🔧 Installation:
1. Download and run HaioSmartApp
2. Install system dependencies as needed
3. Login with your Haio credentials
4. Mount and access your cloud storage

For support: contact@haio.ir
EOF
    
    echo "✅ Release notes created: dist/RELEASE_NOTES.txt"
    
else
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi

echo ""
echo "🎉 Release v1.2.1 build completed successfully!"
