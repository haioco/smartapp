@echo off
REM Haio Smart Solutions - Build Release Script for Windows
REM Version: 1.2.1

echo 🚀 Building Haio Smart Solutions v1.2.1...
echo ===========================================

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install/update dependencies
echo 📋 Installing dependencies...
pip install -r requirements.txt

REM Clean previous builds
echo 🧹 Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec~" del "*.spec~"

REM Clean previous downloads
echo 🧹 Cleaning previous downloads...
if exist "rclone.exe" del "rclone.exe"
if exist "winfsp-installer.msi" del "winfsp-installer.msi"
if exist "rclone-windows.zip" del "rclone-windows.zip"

echo 📥 Downloading bundled dependencies...

REM Download rclone for Windows
echo   - Downloading rclone...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://downloads.rclone.org/rclone-current-windows-amd64.zip' -OutFile 'rclone-windows.zip'}"
if exist "rclone-windows.zip" (
    echo   - Extracting rclone...
    powershell -Command "& {Expand-Archive -Path 'rclone-windows.zip' -DestinationPath 'temp-rclone' -Force}"
    for /r "temp-rclone" %%f in (rclone.exe) do copy "%%f" "rclone.exe" >nul
    rmdir /s /q "temp-rclone"
    del "rclone-windows.zip"
    echo   ✅ rclone downloaded successfully
) else (
    echo   ❌ Failed to download rclone
)

REM Download WinFsp installer
echo   - Downloading WinFsp installer...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/billziss-gh/winfsp/releases/download/v1.12/winfsp-1.12.22339.msi' -OutFile 'winfsp-installer.msi'}"
if exist "winfsp-installer.msi" (
    echo   ✅ WinFsp installer downloaded successfully
) else (
    echo   ❌ Failed to download WinFsp installer
)

REM Build the application
echo 🔨 Building application with PyInstaller...
pyinstaller s3_mounter.spec

REM Check if build was successful
if exist "dist\HaioSmartApp.exe" (
    echo ✅ Build successful!
    echo 📁 Executable location: dist\HaioSmartApp.exe
    echo.
    echo 🎯 Release v1.2.1 Features:
    echo   - Enhanced login dialog with window dragging
    echo   - Professional UI/UX improvements
    echo   - Application icon support
    echo   - Circular logo masking
    echo   - Improved authentication flow
    echo   - Rebranded to 'Haio Smart Solutions'
    echo   - Bundled rclone and WinFsp installer
    echo.
    echo 📋 To distribute:
    echo   1. Copy dist\HaioSmartApp.exe to target systems
    echo   2. Application will offer to install WinFsp automatically
    echo   3. No manual dependency installation required!
    
    echo.
    echo 📄 Creating release notes...
    (
    echo Haio Smart Solutions Client v1.2.1
    echo ==================================
    echo.
    echo 🚀 What's New in v1.2.1:
    echo.
    echo ✨ Enhanced User Experience:
    echo - Professional login dialog with draggable window
    echo - Improved form layouts and component sizing
    echo - Better error handling and user feedback
    echo - Loading states during authentication
    echo.
    echo 🎨 Visual Improvements:
    echo - Rebranded to "Haio Smart Solutions"
    echo - Application icon for taskbar and window
    echo - Circular logo masking for better integration
    echo - Professional styling and color schemes
    echo - Enhanced header design
    echo.
    echo 📦 Bundled Dependencies:
    echo - Includes rclone binary - no separate download needed
    echo - Includes WinFsp installer with automatic installation
    echo - Self-contained application with all dependencies
    echo - One-click installation experience
    echo.
    echo 🐛 Bug Fixes:
    echo - Fixed login window dragging functionality
    echo - Resolved label visibility issues
    echo - Better PyQt6 compatibility
    echo - Removed CSS warnings
    echo.
    echo 📋 System Requirements:
    echo - Windows 10/11
    echo - No additional downloads required
    echo - Application will install WinFsp automatically
    echo.
    echo 🔧 Installation:
    echo 1. Download and run HaioSmartApp.exe
    echo 2. Allow WinFsp installation when prompted
    echo 3. Login with your Haio credentials
    echo 4. Mount and access your cloud storage
    echo.
    echo For support: contact@haio.ir
    ) > dist\RELEASE_NOTES.txt
    
    echo ✅ Release notes created: dist\RELEASE_NOTES.txt
    
) else (
    echo ❌ Build failed! Check the output above for errors.
    exit /b 1
)

echo.
echo 🎉 Release v1.2.1 build completed successfully!
echo 📦 All dependencies are now bundled with the application!
pause
