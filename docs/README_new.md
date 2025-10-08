# Haio Drive Client

A modern cross-platform desktop application for mounting Haio cloud storage buckets as local drives on Windows and Linux systems. Built with PyQt6 for a native look and feel.

## Features

- 🎨 **Modern UI/UX** - Clean, intuitive interface with beautiful styling
- 🔒 **Secure Authentication** - Secure login with token management
- 🌍 **Cross-platform** - Works on both Windows and Linux
- 📁 **Bucket Management** - View, mount, and manage your storage buckets
- 🔄 **Auto-mount** - Optional auto-mount at system boot (Linux only)
- 📦 **Self-contained** - Portable executable with dependency checking
- 💾 **No sudo required** - Mounts to user directory (no root permissions needed)

## Quick Start

### Option 1: Use Pre-built Executable (Recommended)

1. **Download** the latest executable for your platform from the releases page
2. **Run setup** to install dependencies:
   - **Linux**: `./setup_linux.sh`
   - **Windows**: `setup_windows.bat`
3. **Launch** the application:
   - **Linux**: `./HaioDriveClient`
   - **Windows**: `HaioDriveClient.exe`

### Option 2: Run from Source

1. **Clone** this repository
2. **Install dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux
   # or
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python3 main_new.py
   ```

## System Requirements

### Linux
- **Python 3.8+** (if running from source)
- **rclone** - Download from https://rclone.org/
- **FUSE** - Install with `sudo apt-get install fuse`

### Windows
- **Python 3.8+** (if running from source)
- **rclone.exe** - Download from https://rclone.org/downloads/
- **WinFsp** - Download from https://github.com/billziss-gh/winfsp/releases

## Usage

1. **Launch the application**
2. **Login** with your Haio credentials
3. **View your buckets** in the main interface
4. **Mount buckets** by clicking the mount button
5. **Access files** through your file manager at the mount location
6. **Unmount** when finished or close the application

### Mount Locations

Buckets are mounted to user-accessible locations (no sudo required):
- **Linux**: `~/haio-{username}-{bucket-name}`
- **Windows**: `{UserProfile}\haio-{username}-{bucket-name}`

### Auto-mount at Boot (Linux only)

Enable auto-mount to have buckets mounted automatically when your system starts:
1. Click the "Auto-mount at boot" checkbox for any bucket
2. Enter your system password when prompted
3. The bucket will mount automatically on next boot

## Building from Source

### Prerequisites
- Python 3.8+
- pip
- PyInstaller

### Build Steps

**Linux:**
```bash
./build.sh
```

**Windows:**
```bash
build.bat
```

The executable will be created in the `dist/` directory.

## Troubleshooting

### Common Issues

**"Permission denied" errors:**
- Solution: The app now mounts to your home directory, no sudo required

**"rclone not found":**
- Solution: Install rclone or place rclone.exe in the app directory

**"FUSE not available" (Linux):**
- Solution: Install FUSE with `sudo apt-get install fuse`

**"WinFsp not available" (Windows):**
- Solution: Install WinFsp from the GitHub releases page

### Dependency Check

The application automatically checks for required dependencies on startup and provides helpful installation instructions if anything is missing.

## Security Features

- ✅ Secure authentication with token management
- ✅ No credential storage between sessions (optional remember me)
- ✅ GUI password prompts (no terminal password entry)
- ✅ User directory mounting (no root privileges required)

## Support

For issues and questions, please check the troubleshooting section above or refer to the Haio documentation.

## License

MIT License - see LICENSE file for details
