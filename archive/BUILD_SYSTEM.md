# Build System Documentation

This repository includes comprehensive build automation for creating Linux packages with maximum compatibility.

## 🏗️ GitHub Actions Workflows

### Multi-Platform Build (`build-multiplatform.yml`)
- **Triggers**: Push to main, PRs, releases
- **Builds**: Windows, Linux (multiple variants), AppImage
- **Features**: Automatic release asset creation, compatibility testing

### Linux-Focused Build (`build-linux.yml`)
- **Triggers**: Push to main (when relevant files change)
- **Builds**: 4 Linux variants for maximum compatibility
- **Features**: GLIBC requirement analysis, build summaries

## 📦 Linux Package Variants

| Package | Target | Description |
|---------|--------|-------------|
| `HaioSmartApp-linux-modern` | Ubuntu 22.04+ | Latest Python 3.12, modern GLIBC |
| `HaioSmartApp-linux-compat` | Ubuntu 20.04+ | Python 3.9, older GLIBC (better compatibility) |
| `HaioSmartApp-debian12` | Debian 12+ | Built specifically for Debian 12 GLIBC compatibility |
| `HaioSmartApp.AppImage` | Universal | Works on most Linux distributions |

## 🔧 Local Build Scripts

### Linux Compatibility Build
```bash
./build_linux_compat.sh
```
Builds with older Python/GLIBC for better compatibility.

### Docker-based Debian 12 Build
```bash
./build_docker_debian12.sh
```
Uses Docker to build on Debian 12 for perfect compatibility.

### AppImage Build
```bash
./build_appimage.sh
```
Creates universal Linux package that works everywhere.

## 🎯 Solving GLIBC Issues

The original issue:
```
Failed to load Python shared library: GLIBC_2.38 not found
```

**Solutions provided:**
1. **Compatible build** (Ubuntu 20.04 + Python 3.9)
2. **Debian 12 build** (exact target environment)
3. **AppImage** (universal compatibility)

## 🚀 Usage Recommendations

### For Debian 12 users:
Use `HaioSmartApp-debian12` (exact compatibility match)

### For older Linux distributions:
Use `HaioSmartApp-linux-compat` or `HaioSmartApp.AppImage`

### For modern Linux distributions:
Use `HaioSmartApp-linux-modern`

### For maximum portability:
Use `HaioSmartApp.AppImage` (universal)

## 📋 Build Features

- **GLIBC compatibility analysis**
- **Automatic dependency bundling**
- **Cross-platform Windows support**
- **Release automation**
- **Compatibility testing**
- **Build summaries with file sizes**

## 🔍 Debugging Build Issues

Each build includes:
- GLIBC version requirements
- Python version used
- File size and type information
- Compatibility test results

Check the GitHub Actions logs for detailed build information and compatibility matrices.
