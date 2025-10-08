# Migration Guide: v1.6.1 to v1.7.0

## Overview
Version 1.7.0 introduces a major restructure of the codebase for better organization and professionalism. This guide helps you migrate from the old structure to the new one.

## What Changed?

### File Renames
| Old Path | New Path |
|----------|----------|
| `main_new.py` | `src/main.py` |
| `main_old.py` | ❌ Deleted |
| `bucket_browser.py` | `src/ui/dialogs/bucket_browser.py` |
| `share_dialog.py` | `src/ui/dialogs/share_dialog.py` |
| `tempurl_manager.py` | `src/features/tempurl_manager.py` |
| `haio-logo.png` | `resources/icons/haio-logo.png` |
| `test_unmount.py` | `tests/test_unmount.py` |

### Platform Separation
| Old Location | New Location |
|--------------|--------------|
| `build.bat` | `platforms/windows/build.bat` |
| `s3_mounter_windows.spec` | `platforms/windows/s3_mounter_windows.spec` |
| `build.sh` | `platforms/linux/build.sh` |
| `s3_mounter.spec` | `platforms/linux/s3_mounter.spec` |

## For Users

### Running the Application
**Old way:**
```bash
python main_new.py
```

**New way:**
```bash
python src/main.py
```

### Building
**Old way:**
```bash
pyinstaller s3_mounter.spec
```

**New way (Linux):**
```bash
cd platforms/linux
pyinstaller s3_mounter.spec
```

**New way (Windows):**
```bash
cd platforms\windows
pyinstaller s3_mounter_windows.spec
```

## For Developers

### Import Changes
**Old imports:**
```python
from tempurl_manager import TempURLManager
from bucket_browser import BucketBrowserDialog
from share_dialog import ShareDialog
```

**New imports:**
```python
from src.features.tempurl_manager import TempURLManager
from src.ui.dialogs.bucket_browser import BucketBrowserDialog
from src.ui.dialogs.share_dialog import ShareDialog
```

### Running Tests
**Old way:**
```bash
python test_unmount.py
```

**New way:**
```bash
python tests/test_unmount.py
```

## For CI/CD

### GitHub Actions
Workflows have been updated automatically. If you have custom workflows:

**Old:**
```yaml
- name: Build
  run: pyinstaller s3_mounter.spec
```

**New:**
```yaml
- name: Build Linux
  run: |
    cd platforms/linux
    pyinstaller s3_mounter.spec

- name: Build Windows
  run: |
    cd platforms/windows
    pyinstaller s3_mounter_windows.spec
```

## Benefits of New Structure

✅ **Professional naming** - No more `_new`, `_old` suffixes
✅ **Platform separation** - Windows and Linux builds isolated  
✅ **Better organization** - Clear src/, platforms/, resources/ structure
✅ **Easier navigation** - Logical grouping of related files
✅ **Scalable** - Ready for future features and platforms
✅ **Industry standard** - Follows Python packaging best practices

## Compatibility

- ✅ All functionality remains the same
- ✅ No API changes
- ✅ Configuration files unchanged
- ✅ User data and settings preserved
- ⚠️ Build scripts must be updated
- ⚠️ Custom integrations need import updates

## Getting Help

If you encounter issues:
1. Check this migration guide
2. See platform-specific READMEs in `platforms/*/README.md`
3. Open an issue on GitHub

## Rollback

If you need to use the old structure temporarily:
```bash
git checkout v1.6.1
```

However, we recommend migrating to v1.7.0+ for all the benefits above.
