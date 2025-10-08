#!/bin/bash

# Create AppImage for universal Linux compatibility

echo "Creating AppImage for universal Linux compatibility..."
echo "===================================================="

# Download AppImage tools
if [ ! -f "linuxdeploy-x86_64.AppImage" ]; then
    echo "📦 Downloading linuxdeploy..."
    wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
    chmod +x linuxdeploy-x86_64.AppImage
fi

if [ ! -f "linuxdeploy-plugin-python-x86_64.AppImage" ]; then
    echo "🐍 Downloading Python plugin..."
    wget https://github.com/linuxdeploy/linuxdeploy-plugin-python/releases/download/continuous/linuxdeploy-plugin-python-x86_64.AppImage
    chmod +x linuxdeploy-plugin-python-x86_64.AppImage
fi

# Create AppDir structure
mkdir -p HaioSmartApp.AppDir/usr/bin
mkdir -p HaioSmartApp.AppDir/usr/share/applications
mkdir -p HaioSmartApp.AppDir/usr/share/icons/hicolor/256x256/apps

# Copy application
cp main_new.py HaioSmartApp.AppDir/usr/bin/
cp requirements.txt HaioSmartApp.AppDir/usr/bin/
cp haio-logo.png HaioSmartApp.AppDir/usr/share/icons/hicolor/256x256/apps/haiosmartapp.png

# Create desktop file
cat > HaioSmartApp.AppDir/usr/share/applications/haiosmartapp.desktop << EOF
[Desktop Entry]
Type=Application
Name=Haio Smart App
Comment=Smart S3 mounting application
Exec=main_new.py
Icon=haiosmartapp
Categories=Utility;
EOF

# Create AppRun script
cat > HaioSmartApp.AppDir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3/site-packages:${PYTHONPATH}"
cd "${HERE}/usr/bin"
exec python3 main_new.py "$@"
EOF
chmod +x HaioSmartApp.AppDir/AppRun

# Build AppImage
echo "🔨 Building AppImage..."
export LINUXDEPLOY_PLUGIN_PYTHON_APPIMAGE=linuxdeploy-plugin-python-x86_64.AppImage

./linuxdeploy-x86_64.AppImage \
    --appdir HaioSmartApp.AppDir \
    --plugin python \
    --output appimage

if [ -f "Haio_Smart_App-x86_64.AppImage" ]; then
    echo "✅ AppImage created successfully!"
    echo "📍 Location: Haio_Smart_App-x86_64.AppImage"
    echo ""
    echo "🚀 This AppImage should work on most Linux distributions!"
    echo "   Including older systems with GLIBC compatibility issues."
else
    echo "❌ AppImage creation failed"
fi
