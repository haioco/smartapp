# Haio Smart Storage Client v2.0.0 - Release Notes

## 🎉 Major Release - Professional Structure & Bug Fixes

**Release Date**: October 8, 2025  
**Version**: 2.0.0  
**Status**: Production Ready

---

## 🌟 Highlights

### ✨ Complete Professional Restructure
- **86% reduction** in root directory files (50+ → 7)
- Clean, maintainable project structure
- Proper organization by purpose
- Production-ready appearance

### 🐛 Critical Bug Fix
- **Fixed TempURL 401 error**
- Added diagnostic and repair tools
- Complete troubleshooting documentation

### 📚 Documentation Excellence
- Comprehensive project structure guide
- Complete CHANGELOG with version history
- Troubleshooting guides and quick references
- Developer-friendly organization

---

## 📊 What's New

### 🏗️ Structure Improvements

**Before v2.0:**
```
client/
├── 50+ files scattered in root
├── Temporary dev documentation everywhere
├── Scripts mixed with source code
├── Test files in root directory
├── Build artifacts cluttering workspace
└── Multiple venv directories
```

**After v2.0:**
```
client/
├── 7 essential files only
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── requirements.txt
│   ├── .gitignore
│   ├── run.py
│   ├── run.sh
│   └── rclone
├── src/ (all source code)
├── platforms/ (build files by OS)
├── resources/ (icons & assets)
├── tests/ (all test files)
├── scripts/ (utility scripts)
├── docs/ (documentation)
└── archive/ (old artifacts)
```

### 📁 File Organization

| Category | Before | After | Change |
|----------|--------|-------|--------|
| Root Files | 50+ | 7 | -86% |
| Scripts | Scattered | `scripts/` (12) | ✅ Organized |
| Tests | Mixed | `tests/` (4) | ✅ Organized |
| Docs | 40+ scattered | 8 active + 35 archived | ✅ Organized |
| Platform | Mixed | `platforms/{os}/` | ✅ Separated |

### 🔧 Bug Fixes

#### TempURL 401 Error - FIXED ✅

**Problem**: Generated share URLs returned 401 Unauthorized

**Root Cause**: Temp-URL-Key mismatch between local settings and server

**Solution Implemented**:
1. **`scripts/reset_tempurl_key.sh`** - Quick reset tool
   - Backs up settings
   - Removes mismatched key
   - Forces app regeneration

2. **`scripts/fix_tempurl_401.py`** - Interactive fix
   - Tests key configuration
   - Sets new key on server
   - Verifies successful setup

3. **`tests/test_tempurl_diagnostic.py`** - Full diagnostic
   - Tests all TempURL components
   - Detailed error reporting
   - Step-by-step validation

**Documentation Added**:
- `docs/TEMPURL_401_FIX.md` - Complete troubleshooting guide
- `docs/TEMPURL_401_FIXED.md` - Implementation summary

**User Action**: If you get 401 errors, simply logout and login again!

---

## 📥 Installation

### Quick Start

**Linux:**
```bash
# Download and extract
tar -xzf haio-drive-client-linux.tar.gz
cd haio-drive-client-linux

# Run
./run.sh
```

**Windows:**
```powershell
# Extract haio-drive-client-windows.zip
# Double-click HaioSmartApp.exe
```

### From Source

```bash
git clone https://github.com/haioco/smartapp.git
cd smartapp/client

# Install dependencies
pip install -r requirements.txt

# Run
./run.sh           # Linux
python run.py      # Any platform
```

---

## 🔄 Upgrade from v1.x

### Breaking Changes
None! Your data and settings are preserved.

### Migration Steps

1. **Download v2.0.0** release
2. **No configuration changes needed**
3. **TempURL users**: If you get 401 errors:
   ```bash
   # Close app, then:
   rm ~/.config/Haio/SmartApp.conf
   # Restart app and login
   ```

### What's Preserved
- ✅ Your login credentials
- ✅ Saved buckets and mounts
- ✅ Application settings
- ✅ Auto-mount configurations

---

## 🆕 New Features

### Launch Methods

Three convenient ways to run the app:

1. **Shell Script (Linux)**:
   ```bash
   ./run.sh
   ```
   - Auto-detects virtual environment
   - Falls back to system Python

2. **Python Script (Cross-platform)**:
   ```bash
   python run.py
   ```
   - Works on any OS
   - Proper path handling

3. **Python Module**:
   ```bash
   python -m src.main
   ```
   - Cleanest approach
   - Proper module imports

### Diagnostic Tools

1. **TempURL Diagnostic**:
   ```bash
   python tests/test_tempurl_diagnostic.py
   ```
   - Complete TempURL testing
   - Detailed error analysis

2. **TempURL Reset**:
   ```bash
   ./scripts/reset_tempurl_key.sh
   ```
   - Quick fix for 401 errors

3. **Interactive Fix**:
   ```bash
   python scripts/fix_tempurl_401.py
   ```
   - Step-by-step repair

---

## 📖 Documentation

### New Documentation

- **`README.md`** - Main project README (updated)
- **`CHANGELOG.md`** - Complete version history
- **`docs/PROJECT_STRUCTURE.md`** - Detailed structure guide
- **`docs/LAUNCH_METHODS.md`** - How to run the app
- **`docs/TEMPURL_401_FIX.md`** - TempURL troubleshooting
- **`docs/V2.0.0_COMPLETE.md`** - Release summary

### Preserved Documentation

- **`docs/MIGRATION_GUIDE.md`** - Upgrade guide from v1.6.x
- **`docs/QUICK_REF_v1.7.0.md`** - Quick reference
- **`docs/archive/`** - 35+ historical docs preserved

---

## 🔧 Technical Details

### Build System

**PyInstaller Specs Updated**:
- Windows: `platforms/windows/s3_mounter_windows.spec`
- Linux: `platforms/linux/s3_mounter.spec`
- Paths updated for new structure
- Resource paths corrected

**GitHub Actions**:
- Automated builds on tag push
- Multi-platform support
- Automatic release creation

### Dependencies

**Core** (unchanged):
- Python 3.12
- PyQt6 6.7.1
- requests
- rclone

**New Tools**:
- secrets (for secure key generation)
- hmac/hashlib (for TempURL signatures)

---

## 🐛 Known Issues

None! All reported issues fixed in this release.

---

## 🎯 Roadmap

### v2.0.1 (Planned)

**TempURL Improvements**:
- Auto-verify key after setting
- Retry logic with exponential backoff
- Better error messages
- "Reset TempURL Key" button in UI
- Health check before sharing

**UI Enhancements**:
- Progress indicators for long operations
- Better error dialogs
- Improved theme support

---

## 👥 For Developers

### Project Structure

```
client/
├── src/                    # Application code
│   ├── main.py            # Entry point
│   ├── features/          # Features (TempURL, etc.)
│   └── ui/                # UI components
├── platforms/             # Build configs
│   ├── windows/           # Windows builds
│   └── linux/             # Linux builds
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

### Contributing

1. Fork the repository
2. Create feature branch
3. Follow existing structure
4. Add tests for new features
5. Update documentation
6. Submit pull request

### Running Tests

```bash
cd tests
python -m pytest
python test_tempurl.py
python test_tempurl_diagnostic.py
```

---

## 📊 Statistics

### Code Organization

| Metric | v1.7.0 | v2.0.0 | Improvement |
|--------|--------|--------|-------------|
| Root files | 50+ | 7 | 86% ↓ |
| Organized dirs | 5 | 8 | 60% ↑ |
| Doc files | 40+ mixed | 8 + 35 archived | 100% organized |
| Scripts location | Root | scripts/ | ✅ |
| Tests location | Root | tests/ | ✅ |

### File Changes

- **79 files** changed
- **2,111** lines added (mostly docs)
- **450** lines removed (cleanup)
- **6 commits** in this release

---

## 🙏 Acknowledgments

Special thanks to:
- Community feedback that drove the restructure
- Users who reported the TempURL 401 issue
- Everyone testing and providing feedback

---

## 📞 Support

### Getting Help

1. **Documentation**: Check `docs/` folder
2. **Issues**: Open GitHub issue
3. **Discussions**: GitHub Discussions
4. **Email**: support@haio.ir

### Reporting Bugs

When reporting bugs, please include:
- Version number (v2.0.0)
- Operating system
- Steps to reproduce
- Error messages/screenshots
- Output from diagnostic tools (if applicable)

---

## 🔗 Links

- **Repository**: https://github.com/haioco/smartapp
- **Download**: [Releases page](https://github.com/haioco/smartapp/releases/tag/v2.0.0)
- **Documentation**: `docs/` folder in repository
- **Issues**: [GitHub Issues](https://github.com/haioco/smartapp/issues)

---

## 📜 Changelog

See [CHANGELOG.md](../CHANGELOG.md) for complete version history.

---

**Thank you for using Haio Smart Storage Client!** 🎉

We hope v2.0.0 provides you with a cleaner, more professional, and more reliable experience. If you encounter any issues, please don't hesitate to reach out or use our new diagnostic tools!

---

**Version**: 2.0.0  
**Released**: October 8, 2025  
**License**: [Your License]  
**Website**: https://haio.ir
