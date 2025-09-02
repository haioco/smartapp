# -*- mode: python ; coding: utf-8 -*-
import os
import platform
import requests
import zipfile
import shutil

block_cipher = None

# Download rclone if not present
def download_rclone():
    """Download rclone binary for the current platform."""
    if platform.system() == "Windows":
        rclone_url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
        rclone_zip = "rclone-windows.zip"
        rclone_exe = "rclone.exe"
        
        if not os.path.exists(rclone_exe):
            print("Downloading rclone for Windows...")
            try:
                response = requests.get(rclone_url, stream=True)
                response.raise_for_status()
                
                with open(rclone_zip, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract rclone.exe
                with zipfile.ZipFile(rclone_zip, 'r') as zip_ref:
                    for file_info in zip_ref.filelist:
                        if file_info.filename.endswith('rclone.exe'):
                            # Extract just the rclone.exe file
                            file_info.filename = 'rclone.exe'
                            zip_ref.extract(file_info, '.')
                            break
                
                # Cleanup
                os.remove(rclone_zip)
                print("✅ rclone downloaded successfully")
                
            except Exception as e:
                print(f"❌ Failed to download rclone: {e}")
                print("Please download rclone manually from https://rclone.org/downloads/")
    
    elif platform.system() == "Linux":
        rclone_url = "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
        rclone_zip = "rclone-linux.zip"
        rclone_binary = "rclone"
        
        if not os.path.exists(rclone_binary):
            print("Downloading rclone for Linux...")
            try:
                response = requests.get(rclone_url, stream=True)
                response.raise_for_status()
                
                with open(rclone_zip, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract rclone binary
                with zipfile.ZipFile(rclone_zip, 'r') as zip_ref:
                    for file_info in zip_ref.filelist:
                        if file_info.filename.endswith('/rclone'):
                            # Extract just the rclone binary
                            with zip_ref.open(file_info) as source:
                                with open('rclone', 'wb') as target:
                                    shutil.copyfileobj(source, target)
                            os.chmod('rclone', 0o755)  # Make executable
                            break
                
                # Cleanup
                os.remove(rclone_zip)
                print("✅ rclone downloaded successfully")
                
            except Exception as e:
                print(f"❌ Failed to download rclone: {e}")
                print("Please download rclone manually from https://rclone.org/downloads/")

# Download WinFsp installer for Windows
def download_winfsp():
    """Download WinFsp installer for Windows."""
    if platform.system() == "Windows":
        winfsp_url = "https://github.com/billziss-gh/winfsp/releases/download/v1.12/winfsp-1.12.22339.msi"
        winfsp_installer = "winfsp-installer.msi"
        
        if not os.path.exists(winfsp_installer):
            print("Downloading WinFsp installer...")
            try:
                response = requests.get(winfsp_url, stream=True)
                response.raise_for_status()
                
                with open(winfsp_installer, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print("✅ WinFsp installer downloaded successfully")
                
            except Exception as e:
                print(f"❌ Failed to download WinFsp installer: {e}")
                print("Please download WinFsp manually from https://github.com/billziss-gh/winfsp/releases")

# Download dependencies during build
download_rclone()
if platform.system() == "Windows":
    download_winfsp()

# Platform-specific binaries and data files
binaries = []
datas = [
    ('haio-logo.png', '.'),
    ('haio-logo.svg', '.'),
]

if platform.system() == "Windows":
    # Include rclone.exe if it exists
    if os.path.exists("rclone.exe"):
        binaries.append(("rclone.exe", '.'))
    
    # Include WinFsp installer
    if os.path.exists("winfsp-installer.msi"):
        datas.append(("winfsp-installer.msi", '.'))
        
elif platform.system() == "Linux":
    # Include rclone binary if it exists
    if os.path.exists("rclone"):
        binaries.append(("rclone", '.'))

a = Analysis(
    ['main_new.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'requests',
        'urllib3',
        'certifi',
        'json',
        'subprocess',
        'threading',
        'platform',
        'configparser'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HaioSmartApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
