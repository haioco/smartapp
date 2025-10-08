@echo off
echo Smart HAIO App - Windows Build Launcher
echo =======================================
echo.

echo Attempting to run PowerShell build script...
echo This provides better error handling and diagnostics.
echo.

REM Try to run PowerShell script
powershell -ExecutionPolicy Bypass -File build_windows.ps1
if %errorlevel% equ 0 (
    echo.
    echo PowerShell build completed successfully!
    goto :end
)

echo.
echo PowerShell build failed or unavailable, trying batch build...
echo.

REM Fallback to batch script
call build_windows.bat

:end
pause
