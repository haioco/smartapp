# -*- mode: python ; coding: utf-8 -*-
import os
import platform
import requests
import zipfile
import shutil

block_cipher = None

# Download rclone if not present
def download_rclone():
    """Download rclone binary for Windows."""
    print("Downloading rclone for Windows...")
    
    # Force Windows download regardless of current platform
    rclone_filename = "rclone-v1.67.0-windows-amd64.zip"
    rclone_exe = "rclone.exe"
    rclone_url = f"https://downloads.rclone.org/v1.67.0/{rclone_filename}"
    
    print(f"Downloading rclone from: {rclone_url}")
    
    try:
        response = requests.get(rclone_url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(rclone_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract rclone binary
        with zipfile.ZipFile(rclone_filename, 'r') as zip_file:
            # Find the rclone executable in the zip
            for file_info in zip_file.filelist:
                if file_info.filename.endswith(rclone_exe):
                    # Extract just the executable
                    with zip_file.open(file_info) as source:
                        with open(rclone_exe, 'wb') as target:
                            target.write(source.read())
                    break
        
        # Clean up zip file
        os.remove(rclone_filename)
        
        print(f"SUCCESS: rclone downloaded successfully: {rclone_exe}")
        return rclone_exe
        
    except Exception as e:
        print(f"ERROR: Failed to download rclone: {e}")
        return None

# Download WinFsp installer for Windows
def download_winfsp():
    """Download WinFsp installer for Windows builds."""
    print("Downloading WinFsp installer...")
    
    # WinFsp download URLs (try multiple versions, starting with latest)
    winfsp_urls = [
        "https://github.com/winfsp/winfsp/releases/download/v2.1/winfsp-2.1.25156.msi",
        "https://github.com/winfsp/winfsp/releases/download/v2.0/winfsp-2.0.23721.msi",
        "https://github.com/winfsp/winfsp/releases/download/v1.12/winfsp-1.12.22339.msi",
        "https://github.com/winfsp/winfsp/releases/download/v1.11/winfsp-1.11.22176.msi"
    ]
    
    winfsp_path = "winfsp-installer.msi"
    
    for url in winfsp_urls:
        try:
            print(f"Trying to download from: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(winfsp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"SUCCESS: WinFsp installer downloaded successfully: {winfsp_path}")
            return winfsp_path
            
        except Exception as e:
            print(f"FAILED: Could not download from {url}: {e}")
            continue
    
    print("ERROR: Failed to download WinFsp installer from all URLs")
    return None

# Download dependencies during build
print("=== Downloading Windows Dependencies ===")
download_rclone()
download_winfsp()

# Windows-specific binaries and data files
binaries = []
datas = []

# Include optional logo files if they exist
logo_files = ['haio-logo.png', 'haio-logo.svg', 'logo.png', 'icon.ico']
for logo_file in logo_files:
    if os.path.exists(logo_file):
        datas.append((logo_file, '.'))
        print(f"Added {logo_file} to data files")

# Include rclone.exe for Windows
if os.path.exists("rclone.exe"):
    binaries.append(("rclone.exe", '.'))
    print("Added rclone.exe to binaries")

# Include WinFsp installer
if os.path.exists("winfsp-installer.msi"):
    datas.append(("winfsp-installer.msi", '.'))
    print("Added WinFsp installer to data files")

print("=== Building Windows Application ===")

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
        'configparser',
        'os',
        'sys',
        'tempfile',
        'shutil',
        'pathlib',
        'time',
        'logging'
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
    console=False,  # Set to False for GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an .ico file here if you have one
    version=None,  # You can add version info here
)

print("=== Windows Build Configuration Complete ===")
print("Features included:")
print("- Enhanced Windows mounting support")
print("- WinFsp detection and installation")
print("- Windows auto-mount using Task Scheduler")
print("- Cross-platform compatibility")
print("- Bundled rclone and WinFsp")
