# Windows Build Instructions

## Prerequisites
- Python 3.12
- PyInstaller 6.9.0
- All dependencies from `requirements.txt`

## Building

### Quick Build
```bash
cd platforms/windows
build.bat
```

### Release Build
```bash
cd platforms/windows
build_release.bat
```

## Output
The built executable will be in `dist/HaioSmartApp.exe`

## Spec Files
- `s3_mounter_windows.spec` - Main PyInstaller specification file

## Notes
- The build includes rclone.exe for Windows
- Windows Defender may flag the executable - this is normal for PyInstaller builds
- Requires Windows 10 or later
