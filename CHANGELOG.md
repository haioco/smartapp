# Changelog

All notable changes to Haio Smart Storage Client will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-08

### Changed
- **MAJOR CLEANUP**: Removed all unnecessary documentation files and organized structure
  - Archived 35+ temporary markdown files to `docs/archive/`
  - Moved all scripts to `scripts/` directory
  - Moved all tests to `tests/` directory
  - Consolidated platform-specific files to their respective directories
  - Removed old build artifacts, venv, and cache directories
- **Documentation Reorganization**:
  - `README_PROFESSIONAL.md` → `README.md` (main README)
  - Moved version-specific docs to `docs/` directory
  - Created clean, minimal root directory structure
- **Directory Structure**:
  - `/src/` - Application source code only
  - `/platforms/` - Platform-specific build files
  - `/resources/` - Application resources
  - `/tests/` - All test files
  - `/scripts/` - Utility and build scripts
  - `/docs/` - Documentation (archive for old docs)
  - `/archive/` - Old build artifacts and obsolete files

### Removed
- Removed `venv/`, `build/`, `build_env/`, `__pycache__/` directories
- Removed old build artifacts (`.zip` files)
- Removed duplicate and temporary markdown documentation
- Removed deprecated spec files
- Cleaned up 50+ unnecessary files from root directory

### Added
- Clean, professional directory structure suitable for production
- Proper organization of all files by purpose
- Archive directory for historical reference

## [1.7.0] - 2025-10-08

### Changed
- **BREAKING**: Restructured entire codebase for professional organization
  - Moved all source code to `src/` directory
  - Separated platform-specific code into `platforms/windows/` and `platforms/linux/`
  - Moved resources to `resources/` directory
  - Organized tests into `tests/` directory
- Renamed `main_new.py` to `src/main.py`
- Removed deprecated `main_old.py`

### Added
- Launcher scripts for easier app execution:
  - `run.py` - Cross-platform Python launcher
  - `run.sh` - Linux bash launcher with venv auto-detection
  - `src/__main__.py` - Python module entry point
- Professional documentation:
  - `README_PROFESSIONAL.md` - Enhanced README
  - `MIGRATION_GUIDE.md` - Guide for updating to v1.7.0
  - `docs/LAUNCH_METHODS.md` - Documentation of launch options
  - Platform-specific READMEs in `platforms/`
- GitHub Actions workflow updates for new structure

### Fixed
- Module import resolution with new directory structure
- Build system compatibility with restructured paths

## [1.6.1] - 2024-01-XX

### Fixed
- Systemd service cleanup issues on Linux
- Emoji display in folder names (replaced with plain icons)
- Folder navigation in bucket browser
- Stale mount detection and cleanup

### Changed
- Improved error handling for service removal
- Better sync status display

## [1.6.0] - 2024-01-XX

### Added
- **TempURL Feature**: Generate temporary, secure URLs for file sharing
  - Customizable expiration times (1 hour to 7 days)
  - IP address restrictions
  - QR code generation for easy mobile sharing
  - Bulk sharing for multiple files
  - Copy to clipboard functionality
- Enhanced bucket browser with folder navigation
  - Hierarchical folder/file view
  - Breadcrumb navigation
  - Folder-specific operations
- Share dialog improvements:
  - Preset expiration times (Quick Share)
  - Advanced options (Custom)
  - Bulk operations mode
  - QR code viewer

### Changed
- Updated UI theme with better dark mode support
- Improved file browser performance
- Enhanced error messages

### Fixed
- Theme application on system theme change
- Bucket listing performance
- File size display formatting

## [1.5.x] - Previous Versions

### Features
- S3 bucket mounting as local drives
- Auto-mount at system startup
- Credentials management with secure storage
- Bucket statistics and usage display
- Dark mode with system theme detection
- Cross-platform support (Windows & Linux)

---

## Version History Summary

- **v2.0.0**: Major cleanup and organization, production-ready structure
- **v1.7.0**: Professional restructure, improved module organization
- **v1.6.1**: Bug fixes and stability improvements
- **v1.6.0**: TempURL sharing feature, enhanced browser
- **v1.5.x**: Core mounting and management features

[2.0.0]: https://github.com/haioco/smartapp/compare/v1.7.0...v2.0.0
[1.7.0]: https://github.com/haioco/smartapp/compare/v1.6.1...v1.7.0
[1.6.1]: https://github.com/haioco/smartapp/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/haioco/smartapp/compare/v1.5.0...v1.6.0
