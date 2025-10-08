#!/bin/bash

# Linux Compatibility Build Script
# Build on older distributions for maximum compatibility

echo "Creating Linux build with maximum compatibility..."
echo "=================================================="

# Check current GLIBC version
echo "Current GLIBC version:"
ldd --version | head -1

echo ""
echo "Building for maximum Linux compatibility..."

# Use older Python if available, or build in container
if command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
elif command -v python3.8 &> /dev/null; then
    PYTHON_CMD="python3.8"
else
    PYTHON_CMD="python3"
fi

echo "Using Python: $PYTHON_CMD"

# Create virtual environment with older Python
$PYTHON_CMD -m venv venv_compat
source venv_compat/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Build with compatibility flags
echo "Building with compatibility settings..."
pyinstaller s3_mounter.spec \
    --clean \
    --noconfirm \
    --additional-hooks-dir=. \
    --exclude-module=_tkinter \
    --exclude-module=tkinter

echo ""
if [ -f "dist/HaioSmartApp" ]; then
    echo "✓ Compatible Linux build created successfully!"
    echo "Location: dist/HaioSmartApp"
    
    # Check what GLIBC version it requires
    echo ""
    echo "Checking GLIBC requirements:"
    objdump -T dist/HaioSmartApp | grep GLIBC | sort -u | tail -5
else
    echo "❌ Build failed"
fi
