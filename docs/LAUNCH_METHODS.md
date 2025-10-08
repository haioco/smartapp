# Application Launch Methods - v1.7.0

## Problem Solved

After restructuring the app to use a professional `src/` directory structure, the imports weren't working when running `python src/main.py` directly. This is because Python's module system requires proper package initialization.

## Solution

We've created multiple entry points to make launching the app flexible and convenient:

### 1. Launcher Scripts (Recommended)

**Linux/macOS:**
```bash
./run.sh
```
- Auto-detects virtual environment
- Falls back to system Python if venv not found
- Runs app as proper Python module

**Cross-Platform:**
```bash
python run.py
```
- Works on any platform
- Adds client directory to Python path
- Imports and runs main() function

### 2. Python Module Execution

```bash
python -m src.main
```
- Cleanest approach
- Proper module imports
- Python automatically handles paths

### 3. Module Package Execution

```bash
python -m src
```
- Uses `src/__main__.py` as entry point
- Standard Python package pattern

## Technical Details

### Why Direct Execution Fails

Running `python src/main.py` directly fails because:
- Python doesn't recognize `src/` as a package
- Relative imports like `from .features.tempurl_manager` don't work
- The module isn't in Python's module search path

### Why Module Execution Works

Running `python -m src.main` works because:
- Python recognizes `src` as a package
- Adds the parent directory to `sys.path`
- Enables proper relative and absolute imports
- Follows Python's module resolution rules

## Files Added

1. **`src/__main__.py`** - Package entry point for `python -m src`
2. **`run.py`** - Cross-platform launcher script
3. **`run.sh`** - Linux launcher with venv detection

## Build System Compatibility

The PyInstaller spec files in `platforms/windows/` and `platforms/linux/` already use the correct paths and will work with this structure:

```python
Analysis(['../../src/main.py'], ...)
```

PyInstaller handles the module resolution automatically during the build process.

## For Developers

When developing or testing:
- Use `./run.sh` or `python run.py` for quick launches
- Use `python -m src.main` when testing module imports
- Both methods ensure the app runs with correct module structure

## For End Users

The built executables (created by PyInstaller) are standalone and don't require any special launch methods. Just double-click the `.exe` (Windows) or run the binary (Linux).
