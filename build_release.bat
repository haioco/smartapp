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
    echo.
    echo 📋 To distribute:
    echo   1. Copy dist\HaioSmartApp.exe to target systems
    echo   2. Ensure rclone.exe is in PATH or same directory
    echo   3. Ensure WinFsp is installed
    
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
    echo 🐛 Bug Fixes:
    echo - Fixed login window dragging functionality
    echo - Resolved label visibility issues
    echo - Better PyQt6 compatibility
    echo - Removed CSS warnings
    echo.
    echo 📋 System Requirements:
    echo - Windows 10/11
    echo - WinFsp ^(https://github.com/billziss-gh/winfsp/releases^)
    echo - rclone.exe in PATH or same directory
    echo.
    echo 🔧 Installation:
    echo 1. Download and run HaioSmartApp.exe
    echo 2. Install WinFsp if prompted
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
pause
