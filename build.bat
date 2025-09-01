@echo off
REM Build script for Haio Drive Client on Windows

echo Building Haio Drive Client...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Check if rclone.exe is available
where rclone.exe >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "rclone.exe" (
        echo Warning: rclone.exe not found
        echo Please download rclone.exe and place it in this directory
        echo Or ensure rclone is in your PATH
        echo The built application may not work without rclone
    )
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build the application using spec file
echo Building executable with PyInstaller...
pyinstaller s3_mounter.spec

REM Check if build was successful
if exist "dist\HaioDriveClient.exe" (
    echo Build successful!
    echo Executable created at: dist\HaioDriveClient.exe
    
    REM Show file size
    dir dist\HaioDriveClient.exe
    
    echo.
    echo Installation complete!
    echo You can now run the executable: dist\HaioDriveClient.exe
    echo.
    echo Note: The target system must have WinFsp and rclone installed
    echo Run setup_windows.bat on the target system to check dependencies
) else (
    echo Build failed!
    pause
    exit /b 1
)

pause
