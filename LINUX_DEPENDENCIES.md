# Linux Qt Dependencies - Auto Installation Implementation

## Overview
This implementation adds automatic detection and installation of Qt/PyQt6 dependencies required for the Haio Drive Client on Linux systems.

## Problem Solved
Users on Linux systems were encountering GUI-related errors when running the Haio Drive Client due to missing Qt/XCB library dependencies:

```
libxcb-cursor.so.0: cannot open shared object file
libxcb-icccm.so.4: cannot open shared object file
libxcb-image.so.0: cannot open shared object file
libxcb-keysyms.so.1: cannot open shared object file
libxcb-render-util.so.0: cannot open shared object file
libxcb-xinerama.so.0: cannot open shared object file
libxcb-xfixes.so.0: cannot open shared object file
libxkbcommon-x11.so.0: cannot open shared object file
```

## Solution Components

### 1. Enhanced Setup Script (`setup_linux.sh`)
- Auto-detects Linux distribution (Ubuntu/Debian, Fedora/RHEL, Arch, openSUSE)
- Installs Qt6/PyQt6 dependencies using appropriate package manager
- Maintains compatibility with existing rclone and FUSE installation

### 2. Application-Level Dependency Checking (`main_new.py`)
- Added `_check_qt_dependencies()` method to `RcloneManager` class
- Enhanced `check_dependencies()` to include Qt dependency verification
- Added `install_qt_dependencies()` for automatic installation with GUI prompts

### 3. Self-Contained Dependency Installer (`install_dependencies.sh`)
- Standalone script bundled with the application
- Supports multiple Linux distributions
- Can be run independently or called by the application

### 4. Build System Integration
- Updated `s3_mounter.spec` to include dependency scripts in builds
- Modified `build.sh` to reflect new auto-installation capabilities

### 5. Documentation Updates (`README.md`)
- Added troubleshooting section for Linux GUI issues
- Included manual installation commands for different distributions
- Updated feature list to highlight auto-dependency installation

## Required Dependencies
The following packages are automatically installed:

### Ubuntu/Debian (apt):
```bash
libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1
libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0
libxkbcommon-x11-0 qtwayland5
```

### Fedora/RHEL/CentOS (dnf/yum):
```bash
qt6-qtbase qt6-qtwayland libxcb xcb-util-cursor
xcb-util-image xcb-util-keysyms xcb-util-renderutil
xcb-util-wm libxkbcommon-x11
```

### Arch Linux (pacman):
```bash
qt6-base qt6-wayland libxcb xcb-util-cursor
xcb-util-image xcb-util-keysyms xcb-util-renderutil
xcb-util-wm libxkbcommon-x11
```

### openSUSE/SLES (zypper):
```bash
libQt6Core6 libQt6Gui6 libQt6Widgets6 libxcb-cursor0
libxcb-icccm4 libxcb-image0 libxcb-keysyms1
libxcb-render-util0 libxcb-xinerama0 libxkbcommon-x11-0
```

## Usage

### Automatic Installation (Application Level)
1. Run the Haio Drive Client
2. If dependencies are missing, the app will show a dialog
3. Click "Yes" to install automatically
4. Enter system password when prompted
5. Dependencies are installed and application continues

### Manual Installation
```bash
# Option 1: Use enhanced setup script
./setup_linux.sh

# Option 2: Use standalone installer
sudo ./install_dependencies.sh

# Option 3: Manual commands (Ubuntu/Debian)
sudo apt update
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
                 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 \
                 libxkbcommon-x11-0 qtwayland5
```

## Testing
Use the included test script to verify dependency detection:
```bash
python3 test_dependencies.py
```

## Files Modified/Created

### Modified:
- `setup_linux.sh` - Enhanced with Qt dependency installation
- `main_new.py` - Added Qt dependency checking and installation methods
- `s3_mounter.spec` - Include dependency scripts in builds
- `build.sh` - Updated messaging about dependencies
- `README.md` - Added troubleshooting section and installation instructions

### Created:
- `install_dependencies.sh` - Standalone dependency installer
- `test_dependencies.py` - Test script for dependency checking
- `LINUX_DEPENDENCIES.md` - This documentation file

## Benefits

1. **Zero-Configuration Experience**: Users don't need to manually install dependencies
2. **Cross-Distribution Support**: Works on major Linux distributions
3. **Graceful Degradation**: If auto-install fails, provides clear manual instructions
4. **Offline Support**: Bundled scripts work without internet (except for package downloads)
5. **User-Friendly**: GUI prompts guide users through the installation process

## Future Enhancements

1. **Dependency Caching**: Cache installed dependencies to avoid re-checking
2. **Offline Packages**: Bundle .deb/.rpm packages for completely offline installation
3. **AppImage Support**: Create AppImage builds that include all dependencies
4. **Flatpak/Snap**: Package as universal Linux packages with dependencies included

## Compatibility

- Tested on Ubuntu 20.04+, Debian 10+
- Supports Fedora 32+, CentOS 8+, RHEL 8+
- Compatible with Arch Linux and derivatives
- Works with openSUSE Leap 15.3+
- Supports both X11 and Wayland display servers