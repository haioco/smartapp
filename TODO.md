# TODO List - Before Next Release (v1.6.0)

## Current Status
- **Current Version**: 1.5.2 (in development)
- **Latest Release**: 1.5.1
- **Primary File**: `main_new.py` (renamed from main.py)
- **Branch**: main

## ✅ Completed Tasks
1. ✅ Removed old `main.py` file
2. ✅ Pulled remote changes (secure password storage improvements)
3. ✅ Git branch tracking configured (origin/main)
4. ✅ Established `main_new.py` as the primary working file

## 🔨 Tasks Before Next Release

### High Priority

#### 1. Fix Login Form UI (URGENT)
**Issue**: Login form has unreadable field values (white text on light background)
**Screenshot**: User provided screenshot showing the issue
**Required Changes**:
- Redesign login form with better contrast
- Simplify UI layout
- Make field labels and values clearly readable
- Test with both light and dark system themes

**Files to Update**:
- `main_new.py` - LoginDialog class (lines ~2100-2400)

**Design Goals**:
- Clean, modern appearance
- High contrast for readability
- Consistent with app branding (Haio green #4CAF50)
- Professional and user-friendly

---

#### 2. Update File References from main.py to main_new.py
**Affected Files** (found via grep search):
- [ ] `.github/workflows/test-build-v2.yml` - Lines 9, 59, 85, 213, 245
- [ ] `.github/workflows/README.md` - Lines 14, 162, 253
- [ ] `.github/workflows/UPDATES.md` - Lines 18, 28, 136, 175, 239, 247
- [ ] `build_improved.bat` - Line 48
- [ ] `launch.sh` - Lines 20, 23, 25
- [ ] `IMPROVEMENTS.md` - Lines 162, 187
- [ ] `IMPLEMENTATION_COMPLETE.md` - Lines 12, 130, 157, 259, 271
- [ ] `SUMMARY.md` - Lines 142, 166, 232
- [ ] `CHECKLIST.md` - Lines 54, 74, 83
- [ ] `quick-start.sh` - Lines 19, 49
- [ ] `test_improvements.py` - Line 18
- [ ] `.github/copilot-instructions.md` - Line 4

**Action**: Global find/replace `main.py` → `main_new.py` in documentation and build scripts

---

#### 3. Test Login Form Redesign
- [ ] Test on Windows 10/11 with light theme
- [ ] Test on Windows 10/11 with dark theme
- [ ] Test on Linux (Ubuntu) with light theme
- [ ] Test on Linux (Ubuntu) with dark theme
- [ ] Verify field values are readable in all cases
- [ ] Verify "Remember me" checkbox works
- [ ] Test error message display

---

### Medium Priority

#### 4. Update Build Scripts
- [ ] Update PyInstaller spec files to use `main_new.py`
- [ ] Test build on Windows
- [ ] Test build on Linux
- [ ] Verify bundled rclone is included
- [ ] Verify WinFsp detection works

#### 5. Documentation Updates
- [ ] Update README.md with current version info
- [ ] Update installation instructions
- [ ] Add troubleshooting section for login UI issues
- [ ] Update screenshots in documentation

#### 6. Apply Stashed Improvements (if needed)
- [ ] Review stashed changes (`git stash list`)
- [ ] Cherry-pick relevant workflow improvements
- [ ] Test updated CI/CD workflows

---

### Low Priority

#### 7. Code Cleanup
- [ ] Remove any remaining references to old file structure
- [ ] Update code comments to reflect current architecture
- [ ] Remove deprecated functions/classes

#### 8. Testing
- [ ] Run full test suite (`test_improvements.py`)
- [ ] Test mount/unmount on Windows
- [ ] Test mount/unmount on Linux
- [ ] Test auto-mount at boot (Windows Task Scheduler)
- [ ] Test auto-mount at boot (Linux systemd)
- [ ] Test with multiple buckets
- [ ] Test error handling scenarios

---

## 📋 Pre-Release Checklist (v1.6.0)

Before tagging the next release, ensure:

1. **Code Quality**
   - [ ] All TODO items above completed
   - [ ] No syntax errors (`python -m py_compile main_new.py`)
   - [ ] No runtime errors in basic flows
   - [ ] All tests passing

2. **Documentation**
   - [ ] README.md updated
   - [ ] CHANGELOG.md entry added
   - [ ] Version number updated in code
   - [ ] Screenshots updated if UI changed

3. **Testing**
   - [ ] Windows build tested
   - [ ] Linux build tested
   - [ ] Login flow tested
   - [ ] Mount/unmount tested
   - [ ] Auto-mount tested

4. **Git**
   - [ ] All changes committed
   - [ ] Meaningful commit messages
   - [ ] No stray files in staging
   - [ ] Branch synced with origin

---

## 🚀 Release Process (When Ready)

1. Update version in `main_new.py` to `1.6.0`
2. Create CHANGELOG entry
3. Commit changes: `git commit -m "Release v1.6.0"`
4. Create tag: `git tag -a v1.6.0 -m "Version 1.6.0"`
5. Push with tags: `git push origin main --tags`
6. Create GitHub release with binaries
7. Update documentation with release notes

---

## 📝 Notes

- **Login UI Issue**: This is a critical user experience problem that must be fixed before release
- **File Naming**: We've consolidated on `main_new.py` as the single source file
- **Version Strategy**: Using semantic versioning (MAJOR.MINOR.PATCH)
  - 1.5.1 → 1.5.2 (current dev): Bug fixes and UI improvements
  - 1.5.2 → 1.6.0 (next release): When all TODOs complete + login UI fixed

---

## 🔍 Known Issues

1. **Login Form Text Readability** (HIGH)
   - White text on light background makes field values unreadable
   - Affects user experience significantly
   - Screenshot provided by user

2. **File References** (MEDIUM)
   - Many files still reference old `main.py` filename
   - Could cause confusion during builds/testing

---

## 💡 Future Enhancements (Post v1.6.0)

- AI chat feature with bucket data (already stubbed in UI)
- Enhanced dark mode support system-wide
- Better error recovery for mount failures
- Automatic bucket synchronization
- Multi-language support (Persian + English)

---

**Last Updated**: October 7, 2025
**Status**: In active development
