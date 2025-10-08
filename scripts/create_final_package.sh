#!/bin/bash

echo "Preparing Smart HAIO App - FINAL Windows Build Package"
echo "======================================================="
echo

# Create build directory
BUILD_DIR="smarthaioapp-windows-final"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "Copying source files..."
# Copy essential files
cp main_new.py "$BUILD_DIR/"
cp requirements.txt "$BUILD_DIR/"
cp s3_mounter_windows_simple.spec "$BUILD_DIR/"
cp build_simple.bat "$BUILD_DIR/"
cp build_windows_fixed.ps1 "$BUILD_DIR/"

# Copy logo files
cp haio-logo.png "$BUILD_DIR/" 2>/dev/null && echo "✓ haio-logo.png copied"
cp haio-logo.svg "$BUILD_DIR/" 2>/dev/null && echo "✓ haio-logo.svg copied"

# Create simple instructions
cat > "$BUILD_DIR/BUILD_INSTRUCTIONS.txt" << 'EOF'
Smart HAIO App - Windows Build Instructions
==========================================

SIMPLE METHOD (Recommended):
1. Right-click on build_simple.bat
2. Select "Run as administrator" 
3. Wait for build to complete
4. Run dist\HaioSmartApp.exe

ALTERNATIVE METHOD:
1. Open Command Prompt as Administrator
2. Navigate to this folder
3. Run: build_simple.bat

REQUIREMENTS:
- Python 3.9+ installed from python.org
- Run as Administrator
- Internet connection (downloads rclone and WinFsp)

WHAT THIS FIXES:
✓ Windows mounting failures
✓ Auto-mount support for Windows
✓ Enhanced error logging
✓ WinFsp detection and setup
✓ Cross-platform compatibility

The build process will:
1. Install Python dependencies
2. Download rclone for Windows
3. Download WinFsp installer
4. Create HaioSmartApp.exe in dist\ folder

If you get build errors:
- Make sure you're running as Administrator
- Try disabling antivirus temporarily
- Ensure Python is from python.org (not Windows Store)
EOF

echo
echo "Creating FINAL Windows build package..."
zip -r "smarthaioapp-windows-FINAL.zip" "$BUILD_DIR/"

echo
echo "✅ FINAL Windows build package created: smarthaioapp-windows-FINAL.zip"
echo
echo "🎯 SIMPLE INSTRUCTIONS FOR WINDOWS:"
echo "1. Extract smarthaioapp-windows-FINAL.zip"
echo "2. Right-click build_simple.bat → 'Run as administrator'"
echo "3. Wait for completion → run dist\\HaioSmartApp.exe"
echo
echo "Package contents:"
ls -la "$BUILD_DIR/"
echo
echo "Package size:"
ls -lh smarthaioapp-windows-FINAL.zip

# Clean up temp directory
rm -rf "$BUILD_DIR"
