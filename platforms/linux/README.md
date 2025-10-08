# Linux Build Instructions

## Prerequisites
- Python 3.9+ (3.12 recommended)
- PyInstaller 6.9.0
- FUSE libraries: `sudo apt-get install fuse libfuse2`
- All dependencies from `requirements.txt`

## Building

### Quick Build
```bash
cd platforms/linux
./build.sh
```

### Release Build
```bash
cd platforms/linux
./build_release.sh
```

### AppImage Build
```bash
cd platforms/linux
./build_appimage.sh
```

## Output
- Standard build: `dist/HaioSmartApp`
- AppImage: `HaioSmartApp.AppImage`

## Spec Files
- `s3_mounter.spec` - Main PyInstaller specification file

## Desktop Integration
The build includes a `.desktop` file for system menu integration.

## Notes
- Built binaries work on most Linux distributions (Ubuntu 20.04+, Debian 11+)
- For older systems, use the compatibility build
- Requires FUSE for mounting functionality
