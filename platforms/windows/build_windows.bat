@echo off
echo Building Smart HAIO App for Windows...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt
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
echo Trying different PyInstaller execution methods...

REM Try direct pyinstaller command first
pyinstaller s3_mounter_windows_simple.spec --clean --noconfirm 2>nul
if %errorlevel% equ 0 (
    echo ✓ Build successful with direct pyinstaller command
    goto :build_success
)

REM Try python -m pyinstaller
echo Trying: python -m PyInstaller...
python -m PyInstaller s3_mounter_windows_simple.spec --clean --noconfirm
if %errorlevel% equ 0 (
    echo ✓ Build successful with python -m PyInstaller
    goto :build_success
)

REM Try finding PyInstaller in user packages
echo Trying to locate PyInstaller in user packages...
for /f "tokens=*" %%i in ('python -c "import site; print(site.USER_BASE)"') do set USER_BASE=%%i
if exist "%USER_BASE%\Scripts\pyinstaller.exe" (
    echo Found PyInstaller at: %USER_BASE%\Scripts\pyinstaller.exe
    "%USER_BASE%\Scripts\pyinstaller.exe" s3_mounter_windows_simple.spec --clean --noconfirm
    if %errorlevel% equ 0 (
        echo ✓ Build successful with full path to PyInstaller
        goto :build_success
    )
)

REM If all methods fail
echo ERROR: Build failed with all PyInstaller execution methods
echo.
echo Troubleshooting steps:
echo 1. Make sure Python is properly installed (not just Windows Store version)
echo 2. Try installing Python from python.org directly
echo 3. Add Python Scripts directory to PATH
echo 4. Try running: python -m pip install --upgrade pip
pause
exit /b 1

:build_success

echo.
echo Build completed successfully!
echo Executable location: dist\SmartHAIOApp.exe
echo.

REM Check if WinFsp is installed
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
echo You can now run: dist\SmartHAIOApp.exe
pause
