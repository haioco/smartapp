@echo off
echo Smart HAIO App - Simple Windows Build
echo =====================================
echo.

echo NOTE: Using batch build due to PowerShell compatibility issues
echo This is the most reliable method for Windows builds.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Installing PyInstaller...
python -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building Windows executable...
echo This may take several minutes...
echo.

REM Use python -m PyInstaller directly (most reliable method)
python -m PyInstaller s3_mounter_windows_simple.spec --clean --noconfirm
if %errorlevel% equ 0 (
    echo.
    echo ✓ Build completed successfully!
    echo Executable location: dist\HaioSmartApp.exe
    
    REM Check file size
    for %%A in (dist\HaioSmartApp.exe) do echo Executable size: %%~zA bytes
    
    echo.
    echo Checking for WinFsp installation...
    if exist "C:\Program Files\WinFsp" (
        echo ✓ WinFsp found at C:\Program Files\WinFsp
    ) else if exist "C:\Program Files (x86)\WinFsp" (
        echo ✓ WinFsp found at C:\Program Files (x86)\WinFsp
    ) else (
        echo ⚠ WARNING: WinFsp not detected!
        echo Please install WinFsp from: https://winfsp.dev/rel/
        echo This is required for mounting S3 buckets on Windows.
    )
    
    echo.
    echo 🎉 SUCCESS! You can now run: dist\HaioSmartApp.exe
    echo.
    echo Features included in this build:
    echo   ✓ Enhanced Windows mounting with WinFsp detection
    echo   ✓ Windows auto-mount using Task Scheduler
    echo   ✓ Cross-platform compatibility
    echo   ✓ Improved error logging and debugging
    echo   ✓ Modern PyQt6 interface
    
) else (
    echo ❌ Build failed!
    echo.
    echo Common solutions:
    echo 1. Make sure you're running as Administrator
    echo 2. Close any antivirus temporarily during build
    echo 3. Try installing Python from python.org (not Windows Store)
    echo 4. Check that all files are present in the current directory
)

echo.
pause
