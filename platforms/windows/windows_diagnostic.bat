@echo off
echo Smart HAIO App - Windows Dependency Diagnostic
echo =============================================
echo.

echo Checking Python installation...
python --version
echo.

echo Checking WinFsp installation...
if exist "C:\Program Files\WinFsp\" (
    echo ✓ WinFsp found at: C:\Program Files\WinFsp
    dir "C:\Program Files\WinFsp" /b
) else (
    if exist "C:\Program Files (x86)\WinFsp\" (
        echo ✓ WinFsp found at: C:\Program Files (x86)\WinFsp  
        dir "C:\Program Files (x86)\WinFsp" /b
    ) else (
        echo ❌ WinFsp NOT found in standard locations
    )
)

echo.
echo Checking WinFsp service...
sc query WinFsp.Launcher

echo.
echo Checking for rclone...
where rclone 2>nul
if %errorlevel% neq 0 (
    echo rclone not found in PATH, checking app directory...
    if exist "rclone.exe" (
        echo ✓ rclone.exe found in current directory
    ) else (
        echo ❌ rclone.exe not found
    )
)

echo.
echo Checking system PATH for WinFsp...
echo %PATH% | findstr /i winfsp

echo.
echo Registry check for WinFsp...
reg query "HKLM\SOFTWARE\WinFsp" 2>nul
if %errorlevel% neq 0 (
    reg query "HKLM\SOFTWARE\WOW6432Node\WinFsp" 2>nul
)

echo.
echo Diagnostic complete. Please share this output for further troubleshooting.
pause
