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

# Clean previous downloads
echo "🧹 Cleaning previous downloads..."
rm -f rclone
rm -f rclone-linux.zip

echo "📥 Downloading bundled dependencies..."

# Download rclone for Linux
echo "  - Downloading rclone..."
if curl -L "https://downloads.rclone.org/rclone-current-linux-amd64.zip" -o "rclone-linux.zip"; then
    echo "  - Extracting rclone..."
    unzip -q "rclone-linux.zip"
    
    # Find and copy the rclone binary
    find . -name "rclone" -type f -executable -path "*/rclone-*" -exec cp {} ./rclone \;
    chmod +x rclone
    
    # Cleanup
    rm -rf rclone-v*
    rm -f rclone-linux.zip
    
    if [ -f "rclone" ]; then
        echo "  ✅ rclone downloaded successfully"
    else
        echo "  ❌ Failed to extract rclone"
    fi
else
    echo "  ❌ Failed to download rclone"
fi

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
    echo "  - Bundled rclone binary"
    echo ""
    echo "📋 To distribute:"
    echo "  1. Copy dist/HaioSmartApp to target systems"
    echo "  2. On Linux: ensure FUSE is installed (sudo apt-get install fuse)"
    echo "  3. No rclone installation required - it's bundled!"
    
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

📦 Bundled Dependencies:
- Includes rclone binary - no separate download needed
- Self-contained application with minimal external dependencies
- Simplified installation process

🐛 Bug Fixes:
- Fixed login window dragging functionality
- Resolved label visibility issues
- Better PyQt6 compatibility
- Removed CSS warnings

📋 System Requirements:
- Linux (64-bit)
- FUSE support (sudo apt-get install fuse)
- No rclone installation required

🔧 Installation:
1. Download and run HaioSmartApp
2. Install FUSE if not already installed
3. Login with your Haio credentials
4. Mount and access your cloud storage

For support: contact@haio.ir
EOF
    
    echo "✅ Release notes created: dist/RELEASE_NOTES.txt"
    
    # Create a simple installation script
    cat > dist/install.sh << 'EOF'
#!/bin/bash
echo "🚀 Haio Smart Solutions Client Installation"
echo "=========================================="

# Check if FUSE is installed
if ! command -v fusermount &> /dev/null && ! command -v fusermount3 &> /dev/null; then
    echo "📋 FUSE is required but not installed."
    echo "Installing FUSE..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y fuse
    elif command -v yum &> /dev/null; then
        sudo yum install -y fuse
    elif command -v pacman &> /dev/null; then
        sudo pacman -S fuse2
    else
        echo "❌ Unable to install FUSE automatically."
        echo "Please install FUSE manually for your distribution."
        exit 1
    fi
fi

# Make the application executable
chmod +x HaioSmartApp

echo "✅ Installation complete!"
echo "You can now run: ./HaioSmartApp"
EOF
    
    chmod +x dist/install.sh
    echo "✅ Installation script created: dist/install.sh"
    
else
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi

echo ""
echo "🎉 Release v1.2.1 build completed successfully!"
echo "📦 rclone is now bundled with the application!"
