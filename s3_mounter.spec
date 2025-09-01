# -*- mode: python ; coding: utf-8 -*-
import os
import platform

block_cipher = None

# Platform-specific binaries
binaries = []
if platform.system() == "Windows":
    # Try to include rclone.exe if it exists in the current directory
    rclone_path = os.path.join(os.getcwd(), "rclone.exe")
    if os.path.exists(rclone_path):
        binaries.append((rclone_path, '.'))
    else:
        # Fallback: try relative path
        if os.path.exists("rclone.exe"):
            binaries.append(("rclone.exe", '.'))

a = Analysis(
    ['main_new.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
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
    name='S3DriveMounter',
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
