@echo off
echo Smart HAIO App - Simple Diagnostic
echo ===================================
echo.

echo 1. Python Check:
python --version
echo.

echo 2. WinFsp Program Files Check:
if exist "C:\Program Files\WinFsp\bin\winfsp-x64.dll" (
    echo ✓ WinFsp x64 found
) else (
    echo ❌ WinFsp x64 NOT found
)

if exist "C:\Program Files (x86)\WinFsp\bin\winfsp-x86.dll" (
    echo ✓ WinFsp x86 found  
) else (
    echo ❌ WinFsp x86 NOT found
)
echo.

echo 3. WinFsp Service Check:
sc query WinFsp.Launcher > nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ WinFsp service exists
    sc query WinFsp.Launcher | findstr "STATE"
) else (
    echo ❌ WinFsp service NOT found
)
echo.

echo 4. Rclone Check:
if exist rclone.exe (
    echo ✓ rclone.exe found in current directory
) else (
    echo ❌ rclone.exe NOT found in current directory
)
echo.

echo 5. Current Directory:
echo %CD%
echo.

echo 6. Files in current directory:
dir /b *.exe
echo.

echo Done. Please copy this output and share it.
pause
