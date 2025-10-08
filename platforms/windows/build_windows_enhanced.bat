@echo off
REM Haio Smart Solutions - Enhanced Windows Build Script
REM Version: 1.4.0 - Windows Mounting and Auto-mount Fixes

echo Building Haio Smart Solutions v1.4.0 (Windows Enhanced)...
echo ================================================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and ensure it's in your PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "build_env" (
    echo Creating virtual environment...
    python -m venv build_env
)

REM Activate virtual environment
echo Activating virtual environment...
call build_env\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec~" del "*.spec~"

REM Build the application with enhanced Windows support
echo Building application with PyInstaller (Enhanced Windows Support)...
pyinstaller s3_mounter_windows.spec

REM Check if build was successful
if exist "dist\HaioSmartApp.exe" (
    echo ================================================================
    echo SUCCESS: Enhanced Windows build successful!
    echo ================================================================
    echo Executable location: dist\HaioSmartApp.exe
    echo.
    echo Release v1.4.0 Enhanced Features:
    echo   - FIXED: Windows mounting failures with improved WinFsp detection
    echo   - FIXED: Auto-mount now works on Windows using Task Scheduler
    echo   - Enhanced error logging for better troubleshooting
    echo   - Improved Windows compatibility and reliability
    echo   - Cross-platform auto-mount functionality
    echo   - Better WinFsp installation verification
    echo.
    echo Windows-Specific Improvements:
    echo   - Enhanced WinFsp detection using multiple installation paths
    echo   - Improved mounting with Windows-specific rclone options
    echo   - Auto-mount support using Windows Task Scheduler
    echo   - Better error messages for Windows troubleshooting
    echo   - Network drive functionality improvements
    echo.
    echo To test the fixes:
    echo   1. Run HaioSmartApp.exe
    echo   2. Try mounting a bucket (should no longer fail)
    echo   3. Test auto-mount functionality (now works on Windows)
    echo   4. Check logs for detailed error information if issues occur
    
    echo.
    echo Creating enhanced release notes...
    (
    echo Haio Smart Solutions Client v1.4.0 - Windows Enhanced
    echo =====================================================
    echo.
    echo CRITICAL WINDOWS FIXES:
    echo.
    echo 1. Windows Mounting Failures FIXED:
    echo    - Improved WinFsp detection using multiple installation paths
    echo    - Enhanced service verification for WinFsp
    echo    - Added Windows-specific rclone mounting options
    echo    - Better error logging and timeout handling
    echo    - Fixed "failed to mount check the logs" errors
    echo.
    echo 2. Auto-mount Windows Support ADDED:
    echo    - Auto-mount now works on Windows using Task Scheduler
    echo    - Cross-platform auto-mount API
    echo    - No longer limited to Linux systems only
    echo    - Seamless switching between Linux systemd and Windows Task Scheduler
    echo.
    echo Technical Improvements:
    echo - Enhanced _check_winfsp_installation^(^) method
    echo - Improved mount_bucket^(^) with Windows-specific options
    echo - Added create_windows_startup_task^(^) for auto-mount
    echo - Cross-platform auto-mount abstraction
    echo - Better error reporting and user feedback
    echo.
    echo Previous Features ^(from v1.3.0^):
    echo - Bundled rclone and WinFsp dependencies
    echo - Professional UI/UX improvements
    echo - Enhanced login dialog with window dragging
    echo - Application icon support
    echo - Circular logo masking
    echo.
    echo System Requirements:
    echo - Windows 10/11
    echo - WinFsp ^(auto-installed from bundled installer^)
    echo - Administrator privileges for auto-mount setup
    echo.
    echo Installation:
    echo 1. Download and run HaioSmartApp.exe
    echo 2. Accept WinFsp installation if prompted
    echo 3. Login with your Haio credentials
    echo 4. Mount buckets ^(now works reliably on Windows^)
    echo 5. Enable auto-mount ^(now available on Windows^)
    echo.
    echo Troubleshooting:
    echo - Check application logs for detailed error information
    echo - Ensure WinFsp is properly installed
    echo - Run as Administrator for auto-mount functionality
    echo - Verify internet connectivity for cloud storage access
    echo.
    echo For support: contact@haio.ir
    ) > dist\RELEASE_NOTES_v1.4.0.txt
    
    echo Enhanced release notes created: dist\RELEASE_NOTES_v1.4.0.txt
    
) else (
    echo ================================================================
    echo ERROR: Build failed! Check the output above for errors.
    echo ================================================================
    pause
    exit /b 1
)

echo.
echo ================================================================
echo Enhanced Windows build v1.4.0 completed successfully!
echo.
echo IMPORTANT: This build includes critical Windows fixes:
echo - Mounting failures should now be resolved
echo - Auto-mount functionality now works on Windows
echo.
echo Please test both mounting and auto-mount features thoroughly.
echo ================================================================
pause
