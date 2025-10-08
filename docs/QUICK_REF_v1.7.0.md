# Quick Reference - v1.7.0

## 🚀 Launch the App

```bash
# Easiest way
./run.sh

# Or
python run.py

# Or as module
python -m src.main
```

## 🔨 Build the App

**Windows:**
```bash
cd platforms/windows
build.bat
```

**Linux:**
```bash
cd platforms/linux
./build.sh
```

## 📁 Where Things Are

- **Source Code**: `src/`
- **Main Entry**: `src/main.py`
- **Features**: `src/features/`
- **UI Components**: `src/ui/`
- **Windows Builds**: `platforms/windows/`
- **Linux Builds**: `platforms/linux/`
- **Icons/Resources**: `resources/`
- **Tests**: `tests/`
- **Docs**: `docs/`

## 🔧 Development

**Add a new feature:**
```python
# Create in src/features/my_feature.py
# Import in src/main.py
from src.features.my_feature import MyFeature
```

**Add a new dialog:**
```python
# Create in src/ui/dialogs/my_dialog.py
# Import where needed
from src.ui.dialogs.my_dialog import MyDialog
```

## 📝 Key Files

- `README_PROFESSIONAL.md` - Main README
- `CHANGELOG.md` - Version history
- `MIGRATION_GUIDE.md` - Upgrade from v1.6.x
- `docs/LAUNCH_METHODS.md` - How to run the app

## ✅ Testing

```bash
# Run the app
./run.sh

# Check imports work
python -c "from src.features.tempurl_manager import TempURLManager; print('OK')"

# Build and test
cd platforms/linux && ./build.sh
```

## 🐛 Common Issues

**Import errors?**
- Use `python -m src.main` instead of `python src/main.py`
- Or use the launchers: `./run.sh` or `python run.py`

**Build fails?**
- Check paths in spec files use `../../src/main.py`
- Verify resources path: `../../resources/icons/`

## 📦 Release Checklist

- [ ] Test app launches
- [ ] Test builds (Windows & Linux)
- [ ] Update CHANGELOG.md
- [ ] Commit and push changes
- [ ] Tag release: `git tag -a v1.7.0 -m "v1.7.0"`
- [ ] Push tag: `git push origin v1.7.0`
- [ ] Create GitHub release
- [ ] Update documentation

## 🎯 v1.7.0 Status

✅ Restructure complete
✅ Entry points added
✅ Documentation written
✅ Commits pushed
⏳ Builds need testing
⏳ Release tag pending

---

**All changes committed and pushed to GitHub main branch**
