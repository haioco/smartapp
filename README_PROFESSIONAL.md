# Haio Smart Storage Client

Professional cloud storage client application for mounting and managing S3-compatible storage buckets with advanced sharing capabilities.

## 🌟 Features

- **Smart Bucket Management**: Mount S3-compatible storage as local drives
- **Auto-Mount**: Automatic mounting at system startup (Windows & Linux)
- **TempURL Sharing**: Generate temporary, secure URLs for file sharing
  - Customizable expiration times (1 hour to 7 days)
  - IP restrictions
  - QR code generation
  - Bulk sharing support
- **Folder Navigation**: Browse buckets with folder/file hierarchy
- **Dark Mode**: Automatic system theme detection
- **Cross-Platform**: Windows and Linux support

## 📋 Requirements

- Python 3.9+ (3.12 recommended)
- PyQt6 6.7.1
- rclone (automatically downloaded during build)
- **Linux**: FUSE libraries (`libfuse2`)
- **Windows**: WinFsp (for mounting)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/haioco/smartapp.git
cd smartapp/client

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

There are three ways to run the application:

**Option 1: Using the launcher script (Recommended)**
```bash
# Linux/macOS
./run.sh

# Or using Python directly
python run.py
```

**Option 2: Running as a Python module**
```bash
python -m src.main
```

**Option 3: Direct execution (after installing as package)**
```bash
python src/main.py
```

## 🔧 Building

### Windows
```bash
cd platforms/windows
build.bat
```

### Linux
```bash
cd platforms/linux
./build.sh
```

See platform-specific READMEs for detailed build instructions:
- [Windows Build Instructions](platforms/windows/README.md)
- [Linux Build Instructions](platforms/linux/README.md)

## 📁 Project Structure

```
client/
├── src/                    # Application source code
│   ├── main.py            # Main application entry point
│   ├── ui/                # UI components
│   │   └── dialogs/       # Dialog windows
│   └── features/          # Feature modules (TempURL, etc.)
├── platforms/             # Platform-specific build files
│   ├── windows/           # Windows builds
│   └── linux/             # Linux builds
├── resources/             # Application resources
│   └── icons/             # Icons and logos
├── tests/                 # Test files
└── requirements.txt       # Python dependencies
```

## 🎯 Usage

1. **Login**: Enter your credentials to access your storage
2. **Mount Buckets**: View and mount your storage buckets
3. **Browse & Share**: Click "Browse & Share" to navigate files and generate sharing links
4. **Auto-Mount**: Enable auto-mount for automatic mounting at startup

## 🔐 Security

- Credentials stored securely using platform-specific encryption
- TempURL signatures use HMAC-SHA1
- Temporary URLs expire automatically
- Optional IP restrictions for shared files

## 📝 Version

Current version: **1.6.1**

See [CHANGELOG](docs/CHANGELOG.md) for version history.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

[Your License Here]

## 🏢 About

Developed and maintained by **Haio Smart Solutions**

## 🐛 Known Issues

Please check the [Issues](https://github.com/haioco/smartapp/issues) page for known issues and bug reports.

## 💬 Support

For support and questions:
- GitHub Issues: https://github.com/haioco/smartapp/issues
- Email: [Your Support Email]
