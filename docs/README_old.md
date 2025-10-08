# Haio Smart Solutions Client

A professional cross-platform desktop application for mounting cloud storage as local drives on Windows and Linux systems.

## 🚀 Latest Release - v1.3.0

### 📦 Zero-Dependency Installation

Starting with v1.3.0, Haio Smart Solutions Client includes **all required dependencies** for a seamless installation experience:

- ✅ **rclone bundled**: No separate download required
- ✅ **WinFsp installer included** (Windows): Automatic installation with user consent
- ✅ **Self-contained executable**: Works immediately after download
- ✅ **One-click installation**: Download and run - no technical setup required

### ✨ What's New in v1.3.0

- **🎨 Enhanced User Experience**: Professional login dialog with draggable window functionality
- **🏷️ Complete Rebranding**: Updated to "Haio Smart Solutions" with modern visual identity
- **🖼️ Application Icon Support**: Taskbar and window icons for better desktop integration
- **🔄 Circular Logo Masking**: Seamless logo integration without background artifacts
- **⚡ Improved Authentication**: Loading states, error handling, and better user feedback
- **📦 Bundled Dependencies**: Zero manual dependency installation required
- **🛠️ Automatic WinFsp Installation**: Guided installation process on Windows
- **🐛 Bug Fixes**: Resolved login window dragging, label visibility, and PyQt6 compatibility issues

## Features

- **Modern PyQt6 GUI** with professional styling and enhanced user experience
- **Cross-platform support** for Windows and Linux
- **Draggable login dialog** with comprehensive authentication flow
- **User-friendly mounting** to home directory (no root/admin privileges required)
- **GUI password prompts** to prevent terminal blocking
- **Connection testing** before mounting
- **Real-time logging** and status updates
- **Threaded operations** for responsive UI
- **Auto-mount at boot** with systemd integration
- **Application icon** for taskbar and window
- **Portable executables** with all dependencies included
- **Smart unmount handling** with automatic busy device resolution

## Quick Start

### For End Users

1. **Download** the latest release for your platform from the [Releases page](../../releases)
2. **Windows**: Extract `haio-drive-client-windows.zip` and run `HaioSmartApp.exe`
3. **Linux**: Extract `haio-drive-client-linux.tar.gz` and run `./HaioSmartApp`

### For Developers

1. **Clone** the repository:
   ```bash
   git clone <repository-url>
   cd smarthaioapp/client
   ```

2. **Install dependencies**:
   ```bash
   # Linux
   ./setup_linux.sh
   
   # Windows
   setup_windows.bat
   ```

3. **Run from source**:
   ```bash
   python main_new.py
   ```

4. **Build executable**:
   ```bash
   # Linux
   ./build.sh
   
   # Windows
   build.bat
   ```

## Automated Releases

This project uses GitHub Actions for automated building and releasing:

### Release Workflow

- **Triggers**: When you push a version tag (e.g., `v1.0.0`)
- **Builds**: Windows and Linux executables automatically
- **Releases**: Creates GitHub release with downloadable binaries

To create a new release:

```bash
# Tag your commit with a version
git tag v1.0.0
git push origin v1.0.0
```

The workflow will automatically:
1. Build Windows executable with bundled rclone
2. Build Linux executable with bundled rclone  
3. Create GitHub release with both binaries
4. Generate release notes

### Test Build Workflow

- **Triggers**: On pull requests and pushes to main/develop branches
- **Purpose**: Validates that the application builds successfully on both platforms
- **No releases**: Only tests the build process

### Manual Triggers

Both workflows can be manually triggered from the GitHub Actions tab in your repository.

## Architecture

### Main Components

- **`main_new.py`**: Complete Haio Drive Client with modern PyQt6 GUI
- **`RcloneManager`**: Cross-platform rclone integration and dependency checking
- **`PasswordDialog`**: GUI password prompts for system operations
- **`setup_*.sh/bat`**: Automated dependency installation scripts

### Dependencies

- **PyQt6**: Modern GUI framework
- **rclone**: Cloud storage mounting (auto-downloaded during build)
- **FUSE/WinFsp**: Filesystem drivers for mounting
- **requests**: HTTP client for API communication

### Build System

- **PyInstaller**: Creates standalone executables
- **Cross-platform**: Single spec file works on Windows and Linux
- **Dependency bundling**: All Python packages included
- **External tools**: rclone automatically downloaded and bundled

## Configuration

The application stores configuration in:
- **Linux**: `~/.config/haio-drive-client/`
- **Windows**: `%APPDATA%\haio-drive-client`

Mount points are created in:
- **Linux**: `~/haio-mounts/`
- **Windows**: `%USERPROFILE%\haio-mounts`

## Development

### Project Structure

```
client/
├── main_new.py              # Main application
├── requirements.txt         # Python dependencies
├── s3_mounter.spec         # PyInstaller configuration
├── build.sh/build.bat     # Build scripts
├── setup_linux.sh         # Linux dependency installer
├── setup_windows.bat      # Windows dependency installer
├── .github/workflows/      # GitHub Actions
│   ├── release.yml         # Release automation
│   └── test-build.yml      # Build testing
└── .gitignore             # Git exclusions
```

### Adding Features

1. **Modify** `main_new.py` for GUI changes
2. **Update** `requirements.txt` for new Python dependencies
3. **Test** locally with `python main_new.py`
4. **Build** with `./build.sh` or `build.bat`
5. **Commit** and **push** changes
6. **Tag** for release: `git tag v1.x.x && git push origin v1.x.x`

### CI/CD Customization

To modify the build process:

- **Edit** `.github/workflows/release.yml` for release builds
- **Edit** `.github/workflows/test-build.yml` for CI testing
- **Update** `s3_mounter.spec` for PyInstaller configuration

## Contributing

### For Developers

#### Development Workflow

1. **Fork** the repository and create a feature branch
2. **Make changes** and test locally with `python main_new.py`
3. **Build and test** executables with `./build.sh` or `build.bat`
4. **Submit** a pull request to the `main` branch

#### Creating Releases

This project uses automated GitHub Actions workflows for building and releasing binaries:

##### Release Process

1. **Ensure all changes are committed and pushed to main**:
   ```bash
   git add .
   git commit -m "feat: your changes"
   git push origin main
   ```

2. **Create and push a version tag**:
   ```bash
   # Create a new version tag (semantic versioning)
   git tag v1.3.0
   
   # Push the tag to trigger automated release
   git push origin v1.3.0
   ```

3. **Automated build process will**:
   - Build Windows executable (`HaioSmartApp.exe`) with bundled rclone
   - Build Linux executable (`HaioSmartApp`) with bundled rclone
   - Create GitHub release with both binaries
   - Generate automatic release notes

##### Manual Release Trigger

You can also manually trigger a release from GitHub:
1. Go to **Actions** tab in the repository
2. Select **"Build and Release"** workflow
3. Click **"Run workflow"** button
4. Choose the branch and click **"Run workflow"**

##### Release Workflow Details

The release workflow (`.github/workflows/release.yml`) includes:
- **Cross-platform builds** on Windows and Linux runners
- **Automatic dependency management** (downloads latest rclone)
- **Executable packaging** with PyInstaller
- **GitHub release creation** with proper permissions
- **Artifact uploads** for distribution

##### Version Tags

Use semantic versioning for tags:
- `v1.0.0` - Major releases with breaking changes
- `v1.1.0` - Minor releases with new features
- `v1.1.1` - Patch releases with bug fixes

##### Build Testing

The test workflow (`.github/workflows/test-build.yml`) runs automatically on:
- Pull requests to `main` or `develop` branches
- Pushes to `main` or `develop` branches
- Manual triggers from GitHub Actions

This ensures all changes build successfully before merging.

## License

This project is part of the Haio cloud storage ecosystem.
