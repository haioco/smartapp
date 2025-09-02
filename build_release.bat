@echo off
REM Haio Smart Solutions - Build Release Script for Windows
REM Version: 1.3.0

echo Building Haio Smart Solutions v1.3.0...
echo ===========================================

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec~" del "*.spec~"

REM Build the application (rclone and WinFsp will be downloaded automatically)
echo Building application with PyInstaller...
pyinstaller s3_mounter.spec

REM Check if build was successful
if exist "dist\HaioSmartApp.exe" (
    echo SUCCESS: Build successful!
    echo Executable location: dist\HaioSmartApp.exe
    echo.
    echo Release v1.3.0 Features:
    echo   - Bundled rclone and WinFsp dependencies
    echo   - Enhanced login dialog with window dragging
    echo   - Professional UI/UX improvements
    echo   - Application icon support
    echo   - Circular logo masking
    echo   - Improved authentication flow
    echo   - Rebranded to 'Haio Smart Solutions'
    echo.
    echo To distribute:
    echo   1. Copy dist\HaioSmartApp.exe to target systems
    echo   2. Dependencies are now bundled automatically
    echo   3. WinFsp installer included and will auto-install
    
    echo.
    echo Creating release notes...
    (
    echo Haio Smart Solutions Client v1.3.0
    echo ==================================
    echo.
    echo What's New in v1.3.0:
    echo.
    echo Bundled Dependencies:
    echo - Bundled rclone binary - no separate download needed
    echo - WinFsp installer included for Windows
    echo - Auto-installation of missing dependencies
    echo - Fully self-contained application
    echo.
    echo Enhanced User Experience:
    echo - Professional login dialog with draggable window
    echo - Improved form layouts and component sizing
    echo - Better error handling and user feedback
    echo - Loading states during authentication
    echo.
    echo Visual Improvements:
    echo - Rebranded to "Haio Smart Solutions"
    echo - Application icon for taskbar and window
    echo - Circular logo masking for better integration
    echo - Professional styling and color schemes
    echo - Enhanced header design
    echo.
    echo Bug Fixes:
    echo - Fixed login window dragging functionality
    echo - Resolved label visibility issues
    echo - Better PyQt6 compatibility
    echo - Removed CSS warnings
    echo - Fixed Windows build encoding issues
    echo.
    echo System Requirements:
    echo - Windows 10/11
    echo - WinFsp ^(auto-installed from bundled installer^)
    echo - All dependencies bundled with application
    echo.
    echo Installation:
    echo 1. Download and run HaioSmartApp.exe
    echo 2. Accept WinFsp installation if prompted
    echo 3. Login with your Haio credentials
    echo 4. Mount and access your cloud storage
    echo.
    echo For support: contact@haio.ir
    ) > dist\RELEASE_NOTES.txt
    
    echo Release notes created: dist\RELEASE_NOTES.txt
    
) else (
    echo ERROR: Build failed! Check the output above for errors.
    exit /b 1
)

echo.
echo Release v1.3.0 build completed successfully!
pause