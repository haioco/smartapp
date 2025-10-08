#!/usr/bin/env python3
"""
Test script for HAIO Drive Mounter improvements
Run this to verify dark mode detection and other features
"""

import sys
import platform
import subprocess
from pathlib import Path

def test_dark_mode_detection():
    """Test dark mode detection"""
    print("=" * 60)
    print("Testing Dark Mode Detection")
    print("=" * 60)
    
    # Import the ThemeManager from main.py
    sys.path.insert(0, str(Path(__file__).parent))
    from main import ThemeManager
    
    is_dark = ThemeManager.is_dark_mode()
    print(f"System: {platform.system()}")
    print(f"Dark Mode Detected: {is_dark}")
    
    colors = ThemeManager.get_theme_colors(is_dark)
    print(f"\nColor Scheme ({'Dark' if is_dark else 'Light'}):")
    for key, value in colors.items():
        print(f"  {key}: {value}")
    
    print("\n✓ Dark mode detection working!\n")
    return True


def test_windows_utils():
    """Test Windows utilities if on Windows"""
    print("=" * 60)
    print("Testing Windows Utilities")
    print("=" * 60)
    
    if platform.system() != "Windows":
        print("Not on Windows, skipping Windows-specific tests")
        return True
    
    try:
        from windows_utils import (
            is_windows_dark_mode,
            get_windows_mount_drive,
            check_winfsp_installed
        )
        
        # Test dark mode
        dark_mode = is_windows_dark_mode()
        print(f"Windows Dark Mode: {dark_mode}")
        
        # Test drive letter
        drive = get_windows_mount_drive()
        print(f"Next available drive: {drive}")
        
        # Test WinFsp
        installed, message = check_winfsp_installed()
        print(f"WinFsp Status: {message}")
        
        print("\n✓ Windows utilities working!\n")
        return True
    except Exception as e:
        print(f"✗ Windows utilities test failed: {e}\n")
        return False


def test_logging():
    """Test logging setup"""
    print("=" * 60)
    print("Testing Logging System")
    print("=" * 60)
    
    log_dir = Path.home() / '.config' / 'haio-mounter'
    log_file = log_dir / 'app.log'
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    print(f"Log directory: {log_dir}")
    print(f"Log file: {log_file}")
    
    # Write test log
    logging.info("Test log entry - HAIO Drive Mounter")
    logging.warning("Test warning - This is a test")
    logging.error("Test error - This is a test")
    
    if log_file.exists():
        print(f"✓ Log file created successfully")
        print(f"Log file size: {log_file.stat().st_size} bytes")
        print("\n✓ Logging system working!\n")
        return True
    else:
        print("✗ Log file not created\n")
        return False


def test_dependencies():
    """Test required dependencies"""
    print("=" * 60)
    print("Testing Dependencies")
    print("=" * 60)
    
    dependencies = {
        'PyQt6': False,
        'requests': False,
        'rclone': False
    }
    
    # Test Python modules
    try:
        import PyQt6
        dependencies['PyQt6'] = True
        print(f"✓ PyQt6 installed (version: {PyQt6.QtCore.PYQT_VERSION_STR})")
    except ImportError:
        print("✗ PyQt6 not installed")
    
    try:
        import requests
        dependencies['requests'] = True
        print(f"✓ requests installed (version: {requests.__version__})")
    except ImportError:
        print("✗ requests not installed")
    
    # Test rclone
    try:
        result = subprocess.run(
            ['rclone', 'version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            dependencies['rclone'] = True
            print(f"✓ rclone installed ({version_line})")
        else:
            print("✗ rclone command failed")
    except FileNotFoundError:
        print("✗ rclone not found in PATH")
    except Exception as e:
        print(f"✗ rclone check failed: {e}")
    
    all_ok = all(dependencies.values())
    if all_ok:
        print("\n✓ All dependencies installed!\n")
    else:
        print("\n✗ Some dependencies missing. Install with:")
        print("  pip install -r requirements.txt")
        if not dependencies['rclone']:
            print("  Install rclone from https://rclone.org/downloads/\n")
    
    return all_ok


def test_config_directory():
    """Test configuration directory creation"""
    print("=" * 60)
    print("Testing Configuration Directory")
    print("=" * 60)
    
    config_dir = Path.home() / '.config' / 'haio-mounter'
    config_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Config directory: {config_dir}")
    
    if config_dir.exists() and config_dir.is_dir():
        print(f"✓ Config directory exists")
        print(f"Permissions: {oct(config_dir.stat().st_mode)[-3:]}")
        print("\n✓ Configuration directory working!\n")
        return True
    else:
        print("✗ Failed to create config directory\n")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("HAIO DRIVE MOUNTER - IMPROVEMENT TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Configuration Directory", test_config_directory),
        ("Logging System", test_logging),
        ("Dark Mode Detection", test_dark_mode_detection),
    ]
    
    if platform.system() == "Windows":
        tests.append(("Windows Utilities", test_windows_utils))
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"✗ {name} test crashed: {e}\n")
            results[name] = False
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready.\n")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
