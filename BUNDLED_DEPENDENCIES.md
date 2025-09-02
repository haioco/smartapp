# Haio Smart Solutions - Bundled Dependencies

## Overview

Starting with version 1.2.1, Haio Smart Solutions Client includes all necessary dependencies to provide a seamless installation experience for users.

## Bundled Components

### Windows
- **rclone.exe**: Cloud storage mounting utility (automatically downloaded during build)
- **WinFsp Installer**: Windows filesystem driver (winfsp-1.12.22339.msi)
- **Application Assets**: Logo files and other resources

### Linux
- **rclone**: Cloud storage mounting utility (automatically downloaded during build)
- **Application Assets**: Logo files and other resources

## Build Process

### Automatic Dependency Download

The PyInstaller spec file (`s3_mounter.spec`) automatically downloads dependencies during the build process:

1. **rclone**: Downloaded from official rclone.org releases
   - Windows: `rclone-current-windows-amd64.zip`
   - Linux: `rclone-current-linux-amd64.zip`

2. **WinFsp** (Windows only): Downloaded from GitHub releases
   - File: `winfsp-1.12.22339.msi`
   - Version: 1.12 (latest stable)

### Build Scripts

Enhanced build scripts handle dependency management:

- **Windows**: `build_release.bat`
  - Downloads rclone and WinFsp installer
  - Builds self-contained executable
  - Creates installation notes

- **Linux**: `build_release.sh` 
  - Downloads rclone binary
  - Creates installation script for FUSE
  - Builds self-contained executable

## Runtime Dependency Handling

### Application Startup
1. Checks for bundled rclone in application directory
2. Falls back to system PATH if bundled version not found
3. On Windows: Offers automatic WinFsp installation if missing

### User Experience
- **No manual downloads required**
- **Automatic dependency installation** (WinFsp on Windows)
- **Clear error messages** with guided installation steps
- **Fallback mechanisms** for missing dependencies

## File Locations

### Bundled with Application
```
HaioSmartApp.exe/           # Windows executable
├── rclone.exe              # Bundled rclone
├── winfsp-installer.msi    # WinFsp installer
├── haio-logo.png          # Application logo
└── haio-logo.svg          # Vector logo

HaioSmartApp               # Linux executable
├── rclone                 # Bundled rclone (executable)
├── haio-logo.png         # Application logo
└── haio-logo.svg         # Vector logo
```

### Runtime Search Order
1. Application directory (bundled)
2. System PATH
3. Common installation locations
4. User-specific locations

## Size Impact

Approximate file sizes:
- **rclone**: ~50MB (Windows), ~45MB (Linux)
- **WinFsp installer**: ~2MB
- **Total increase**: ~52MB per platform

## Benefits

1. **User-Friendly**: No technical knowledge required
2. **Self-Contained**: Works offline after download
3. **Version Consistency**: Tested rclone version included
4. **Automatic Updates**: Dependencies updated with app releases
5. **Support Simplification**: Fewer environment-related issues

## Future Considerations

- **Delta Updates**: Only download changed components
- **Compression**: Further reduce distribution size
- **Optional Components**: Allow users to skip certain dependencies
- **Auto-Update**: Update dependencies independently of app updates

## Technical Notes

### Security
- All downloads use HTTPS
- Checksums could be added for verification
- Downloads from official sources only

### Compatibility
- Windows: Supports Windows 10/11 (64-bit)
- Linux: Supports most modern distributions (64-bit)
- rclone: Latest stable version ensures compatibility

### Error Handling
- Graceful fallbacks for download failures
- Clear error messages for users
- Support contact information provided
