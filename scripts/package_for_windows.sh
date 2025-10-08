#!/bin/bash

echo "Preparing Smart HAIO App for Windows VM build..."
echo

# Create build directory
BUILD_DIR="smarthaioapp-windows-build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "Copying source files..."
# Copy essential files
cp main_new.py "$BUILD_DIR/"
cp requirements.txt "$BUILD_DIR/"
cp s3_mounter_windows_simple.spec "$BUILD_DIR/"
cp build_windows.bat "$BUILD_DIR/"
cp build_windows.ps1 "$BUILD_DIR/"
cp build_launcher.bat "$BUILD_DIR/"
cp build_windows_vm.md "$BUILD_DIR/README.md"

# Copy assets if they exist
if [ -d "assets" ]; then
    cp -r assets "$BUILD_DIR/"
    echo "✓ Assets copied"
fi

# Copy images if they exist
for img in logo.png icon.ico haio-logo.png haio-logo.svg; do
    if [ -f "$img" ]; then
        cp "$img" "$BUILD_DIR/"
        echo "✓ $img copied"
    fi
done

echo
echo "Creating Windows build package..."
zip -r "smarthaioapp-windows-build.zip" "$BUILD_DIR/"

echo
echo "✓ Windows build package created: smarthaioapp-windows-build.zip"
echo
echo "Transfer this zip file to your Windows VM and:"
echo "1. Extract the zip file"
echo "2. Open Command Prompt as Administrator"
echo "3. Navigate to the extracted folder"
echo "4. Run ONE of these build options:"
echo "   - build_launcher.bat    (Recommended - tries PowerShell then batch)"
echo "   - build_windows.ps1     (PowerShell version - best error handling)"
echo "   - build_windows.bat     (Batch version - basic compatibility)"
echo
echo "Size of package:"
ls -lh smarthaioapp-windows-build.zip

# Clean up temp directory
rm -rf "$BUILD_DIR"
