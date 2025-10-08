@echo off
REM Improved Windows Build Script for HAIO S3 Drive Mounter
REM This creates a fully self-contained single executable

echo ========================================
echo HAIO Drive Mounter - Windows Build
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from python.org
    pause
    exit /b 1
)

echo [1/6] Checking dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

REM Check for rclone
echo [2/6] Checking for rclone...
if not exist "rclone.exe" (
    echo WARNING: rclone.exe not found in current directory
    echo Downloading rclone...
    powershell -Command "Invoke-WebRequest -Uri 'https://downloads.rclone.org/rclone-current-windows-amd64.zip' -OutFile 'rclone.zip'"
    powershell -Command "Expand-Archive -Path 'rclone.zip' -DestinationPath '.' -Force"
    move rclone-*-windows-amd64\rclone.exe .
    rmdir /s /q rclone-*-windows-amd64
    del rclone.zip
)

REM Check for WinFsp
echo [3/6] Checking WinFsp installation...
reg query "HKLM\SOFTWARE\WinFsp" >nul 2>&1
if errorlevel 1 (
    echo WARNING: WinFsp not detected
    echo Users will need to install WinFsp from https://winfsp.dev/
    echo Build will continue...
)

echo [4/6] Creating build spec file...
echo # -*- mode: python ; coding: utf-8 -*- > haio_improved.spec
echo a = Analysis( >> haio_improved.spec
echo     ['main.py'], >> haio_improved.spec
echo     pathex=[], >> haio_improved.spec
echo     binaries=[('rclone.exe', '.')], >> haio_improved.spec
echo     datas=[], >> haio_improved.spec
echo     hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'requests'], >> haio_improved.spec
echo     hookspath=[], >> haio_improved.spec
echo     hooksconfig={}, >> haio_improved.spec
echo     runtime_hooks=[], >> haio_improved.spec
echo     excludes=[], >> haio_improved.spec
echo     noarchive=False, >> haio_improved.spec
echo ) >> haio_improved.spec
echo pyz = PYZ(a.pure) >> haio_improved.spec
echo exe = EXE( >> haio_improved.spec
echo     pyz, >> haio_improved.spec
echo     a.scripts, >> haio_improved.spec
echo     a.binaries, >> haio_improved.spec
echo     a.datas, >> haio_improved.spec
echo     [], >> haio_improved.spec
echo     name='HaioSmartDriveMounter', >> haio_improved.spec
echo     debug=False, >> haio_improved.spec
echo     bootloader_ignore_signals=False, >> haio_improved.spec
echo     strip=False, >> haio_improved.spec
echo     upx=True, >> haio_improved.spec
echo     upx_exclude=[], >> haio_improved.spec
echo     runtime_tmpdir=None, >> haio_improved.spec
echo     console=False, >> haio_improved.spec
echo     disable_windowed_traceback=False, >> haio_improved.spec
echo     argv_emulation=False, >> haio_improved.spec
echo     target_arch=None, >> haio_improved.spec
echo     codesign_identity=None, >> haio_improved.spec
echo     entitlements_file=None, >> haio_improved.spec
echo     icon='haio-logo.png' if exist('haio-logo.png') else None, >> haio_improved.spec
echo ) >> haio_improved.spec

echo [5/6] Building executable...
pyinstaller --clean --noconfirm haio_improved.spec

if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo [6/6] Creating distribution package...
if not exist "dist\HaioSmartDriveMounter-Windows" mkdir "dist\HaioSmartDriveMounter-Windows"
copy dist\HaioSmartDriveMounter.exe dist\HaioSmartDriveMounter-Windows\
copy rclone.exe dist\HaioSmartDriveMounter-Windows\ 2>nul

REM Create README
echo HAIO Smart Drive Mounter - Windows Edition > dist\HaioSmartDriveMounter-Windows\README.txt
echo. >> dist\HaioSmartDriveMounter-Windows\README.txt
echo Requirements: >> dist\HaioSmartDriveMounter-Windows\README.txt
echo - Windows 10/11 >> dist\HaioSmartDriveMounter-Windows\README.txt
echo - WinFsp (Download from https://winfsp.dev/) >> dist\HaioSmartDriveMounter-Windows\README.txt
echo. >> dist\HaioSmartDriveMounter-Windows\README.txt
echo Installation: >> dist\HaioSmartDriveMounter-Windows\README.txt
echo 1. Install WinFsp if not already installed >> dist\HaioSmartDriveMounter-Windows\README.txt
echo 2. Run HaioSmartDriveMounter.exe >> dist\HaioSmartDriveMounter-Windows\README.txt
echo. >> dist\HaioSmartDriveMounter-Windows\README.txt
echo Note: rclone.exe is included in this package >> dist\HaioSmartDriveMounter-Windows\README.txt

REM Create installer script
echo Creating installer script...
echo [Setup] > haio_installer.iss
echo AppName=HAIO Smart Drive Mounter >> haio_installer.iss
echo AppVersion=2.0 >> haio_installer.iss
echo DefaultDirName={autopf}\HAIO >> haio_installer.iss
echo DefaultGroupName=HAIO >> haio_installer.iss
echo OutputBaseFilename=HaioSmartDriveMounter-Setup >> haio_installer.iss
echo Compression=lzma2 >> haio_installer.iss
echo SolidCompression=yes >> haio_installer.iss
echo [Files] >> haio_installer.iss
echo Source: "dist\HaioSmartDriveMounter-Windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs >> haio_installer.iss
echo [Icons] >> haio_installer.iss
echo Name: "{group}\HAIO Drive Mounter"; Filename: "{app}\HaioSmartDriveMounter.exe" >> haio_installer.iss
echo Name: "{autodesktop}\HAIO Drive Mounter"; Filename: "{app}\HaioSmartDriveMounter.exe" >> haio_installer.iss

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo Executable location: dist\HaioSmartDriveMounter.exe
echo Package location: dist\HaioSmartDriveMounter-Windows\
echo.
echo To create an installer, install Inno Setup and run:
echo   iscc haio_installer.iss
echo.
pause
