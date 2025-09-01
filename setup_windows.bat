@echo off
REM Setup script for Haio Drive Client on Windows

echo Setting up Haio Drive Client for Windows...

REM Check if WinFsp is installed
if exist "C:\Program Files\WinFsp\bin\launchctl-x64.exe" (
    echo ✓ WinFsp is already installed
) else if exist "C:\Program Files (x86)\WinFsp\bin\launchctl-x64.exe" (
    echo ✓ WinFsp is already installed
) else (
    echo ✗ WinFsp is not installed
    echo Please download and install WinFsp from:
    echo https://github.com/billziss-gh/winfsp/releases
    echo.
    echo After installing WinFsp, run this script again.
    pause
    exit /b 1
)

REM Check if rclone exists
where rclone.exe >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ rclone is available in PATH
) else (
    REM Check if rclone.exe is in the current directory
    if exist "rclone.exe" (
        echo ✓ rclone.exe found in current directory
    ) else (
        echo ✗ rclone.exe not found
        echo.
        echo Please download rclone.exe from:
        echo https://rclone.org/downloads/
        echo.
        echo Either:
        echo 1. Add rclone.exe to your PATH, or
        echo 2. Place rclone.exe in the same directory as this script
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ✓ Setup completed successfully!
echo.
echo You can now run the Haio Drive Client:
echo   python main_new.py
echo.
echo Or build a standalone executable:
echo   build.bat
echo.
pause
