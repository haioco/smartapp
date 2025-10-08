# GitHub Workflows Guide

This directory contains GitHub Actions workflows for building and testing the HAIO Drive Mounter application.

## 📋 Available Workflows

### 1. **test-build-v2.yml** ⭐ (RECOMMENDED)
**Purpose**: Comprehensive test builds for Windows & Linux with v2.0 improvements

**Triggers**:
- Pull requests to `main` or `develop`
- Pushes to `main` or `develop`
- Manual workflow dispatch
- Changes to `main.py`, `windows_utils.py`, `requirements.txt`, or `*.spec` files

**What it does**:
- ✅ Builds Windows executable with embedded rclone
- ✅ Builds Linux executables for Ubuntu 22.04 and 20.04
- ✅ Runs syntax checks
- ✅ Runs test suite (`test_improvements.py`)
- ✅ Verifies GLIBC compatibility
- ✅ Uploads build artifacts (7-day retention)
- ✅ Creates comprehensive build summary

**Features tested**:
- Dark mode support
- Mount stability improvements
- Health monitoring
- Comprehensive logging
- Windows-specific utilities

**Artifacts**:
- `windows-build-{sha}` - Windows .exe
- `linux-build-Ubuntu-{version}-{sha}` - Linux binaries
- `*-build-info-{sha}` - Build information files

---

### 2. **test-build.yml** (Legacy)
**Purpose**: Original test build workflow (updated for v2.0 compatibility)

**Triggers**:
- Pull requests to `main` or `develop`
- Pushes to `main` or `develop`
- Manual workflow dispatch

**What it does**:
- Builds Windows executable
- Builds Linux executable
- Basic syntax checks
- Runs test suite

**Note**: This workflow is maintained for compatibility but **test-build-v2.yml is recommended** for new builds.

---

### 3. **build-multiplatform.yml**
**Purpose**: Multi-platform package generation

**Triggers**:
- Pushes to `main`
- Pull requests to `main`
- Published releases

**What it builds**:
- Windows executable (latest Ubuntu runner)
- Linux normal executable (Ubuntu 22.04)
- Linux compatible executable (Ubuntu 20.04 for better GLIBC compatibility)
- Linux Debian 12 build (Docker-based)
- AppImage (universal Linux package)

**Special features**:
- Tests builds on multiple Linux distributions
- Creates release assets on GitHub releases
- Generates SHA256 checksums

---

### 4. **build-linux.yml**
**Purpose**: Specialized Linux builds

**Triggers**:
- Pushes to `main` (when specific files change)
- Pull requests to `main`

**What it builds**:
- Modern Linux (Ubuntu 22.04 + Python 3.12)
- Compatible Linux (Ubuntu 20.04 + Python 3.9)
- Debian 12 Docker build
- Universal AppImage

**Features**:
- Shows GLIBC requirements for each build
- Provides detailed system information
- Creates comprehensive build summary

---

## 🚀 Quick Start

### Run Test Build Manually

1. Go to **Actions** tab in GitHub
2. Select **"Test Build v2.0 - Windows & Linux"**
3. Click **"Run workflow"**
4. Select branch
5. Click **"Run workflow"**

### Download Build Artifacts

1. Go to **Actions** tab
2. Click on a completed workflow run
3. Scroll to **Artifacts** section
4. Download the build you need

---

## 📦 Build Outputs

### Windows Build
- **File**: `HaioSmartDriveMounter.exe`
- **Size**: ~40-60 MB (with embedded rclone)
- **Requirements**: 
  - Windows 10/11
  - WinFsp (for mounting)
- **Includes**:
  - PyQt6 GUI
  - Dark mode support
  - Windows-specific utilities
  - Embedded rclone

### Linux Builds

#### Ubuntu 22.04 (Modern)
- **File**: `HaioSmartDriveMounter-ubuntu2204`
- **Python**: 3.12
- **GLIBC**: 2.35+
- **Best for**: Ubuntu 22.04+, Fedora 36+, Debian 12+

#### Ubuntu 20.04 (Compatible)
- **File**: `HaioSmartDriveMounter-ubuntu2004`
- **Python**: 3.10
- **GLIBC**: 2.31+
- **Best for**: Ubuntu 20.04+, older systems

#### Debian 12
- **File**: `HaioSmartDriveMounter-debian12`
- **Built with**: Docker (Debian 12)
- **Best for**: Debian-based distributions

#### AppImage (Universal)
- **File**: `HaioSmartApp.AppImage`
- **Works on**: Most Linux distributions
- **Portable**: Single file, no installation needed

---

## 🧪 Testing

### Automated Tests
All workflows run:
1. **Syntax check**: `python -m py_compile main.py windows_utils.py`
2. **Test suite**: `python test_improvements.py`
3. **Build verification**: Checks if executable exists
4. **Dependency analysis**: GLIBC requirements (Linux)

### Manual Testing
After downloading artifacts:

#### Windows:
```cmd
# Run directly (requires WinFsp)
HaioSmartDriveMounter.exe

# Check for WinFsp
reg query "HKLM\SOFTWARE\WinFsp"
```

#### Linux:
```bash
# Make executable
chmod +x HaioSmartDriveMounter-*

# Run
./HaioSmartDriveMounter-ubuntu2204

# Check logs
cat ~/.config/haio-mounter/app.log
```

---

## 📊 Build Matrix

| Workflow | Windows | Linux (22.04) | Linux (20.04) | Debian 12 | AppImage |
|----------|---------|---------------|---------------|-----------|----------|
| test-build-v2.yml | ✅ | ✅ | ✅ | ❌ | ❌ |
| test-build.yml | ✅ | ✅ | ❌ | ❌ | ❌ |
| build-multiplatform.yml | ✅ | ✅ | ✅ | ✅ | ✅ |
| build-linux.yml | ❌ | ✅ | ✅ | ✅ | ✅ |

---

## 🔧 Configuration

### Environment Variables
Workflows use these common settings:
```yaml
env:
  PYTHON_VERSION: '3.12'
  APP_NAME: 'HaioSmartDriveMounter'
```

### Dependencies
Required in `requirements.txt`:
- PyQt6 >= 6.7.1
- requests >= 2.28.0
- pyinstaller == 6.9.0

### System Requirements

**Windows Runner**:
- windows-latest
- Python 3.12
- PowerShell

**Linux Runner**:
- ubuntu-22.04 or ubuntu-20.04
- Python 3.10-3.12
- fuse, libfuse2, build-essential

---

## 📝 Customization

### Add New Platform
Edit `test-build-v2.yml`, add to matrix:
```yaml
- name: "Ubuntu 24.04"
  os: ubuntu-24.04
  python: "3.13"
  output: "HaioSmartDriveMounter-ubuntu2404"
```

### Change Build Options
Modify PyInstaller command:
```yaml
pyinstaller \
  --name="YourAppName" \
  --onefile \
  --windowed \
  --icon=your-icon.ico \
  main.py
```

### Add More Tests
Add step before build:
```yaml
- name: Run custom tests
  run: |
    pytest tests/
    python -m unittest discover
```

---

## 🐛 Troubleshooting

### Build Fails on Windows
**Issue**: `pip install` errors  
**Solution**: Update `requirements.txt`, use `pip install --upgrade pip`

**Issue**: Missing rclone  
**Solution**: Workflow auto-downloads rclone, check download step logs

### Build Fails on Linux
**Issue**: GLIBC errors  
**Solution**: Use Ubuntu 20.04 runner or Debian 12 Docker build

**Issue**: Missing system packages  
**Solution**: Add to "Install system dependencies" step

### Artifacts Not Uploaded
**Issue**: `actions/upload-artifact@v4` fails  
**Solution**: Check if dist/ directory exists and contains files

---

## 📚 Resources

### GitHub Actions Docs
- [Workflow syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Available runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners)
- [Artifacts](https://docs.github.com/en/actions/guides/storing-workflow-data-as-artifacts)

### PyInstaller
- [Documentation](https://pyinstaller.org/)
- [Spec files](https://pyinstaller.org/en/stable/spec-files.html)
- [Options](https://pyinstaller.org/en/stable/usage.html)

### Project Docs
- `IMPROVEMENTS.md` - Technical improvements
- `IMPLEMENTATION_COMPLETE.md` - Implementation details
- `SUMMARY.md` - Quick overview

---

## 🎯 Best Practices

1. **Always test locally first** before pushing
2. **Use test-build-v2.yml** for comprehensive testing
3. **Check build artifacts** after workflow completes
4. **Review GLIBC requirements** for Linux builds
5. **Test on target platform** before release
6. **Keep requirements.txt updated**
7. **Document build changes** in commit messages

---

## 📈 Build Status

Check current build status:
- View [Actions tab](../../actions) in repository
- Look for green checkmarks ✅
- Download artifacts from successful builds
- Review build summaries for details

---

**Last Updated**: October 7, 2025  
**Version**: 2.0  
**Workflows**: 4 active
