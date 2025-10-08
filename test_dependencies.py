#!/usr/bin/env python3
"""
Test script for dependency checking functionality
"""

import sys
import os
import platform

# Add the current directory to path so we can import main_new
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main_new import RcloneManager
    
    def test_dependency_check():
        """Test the dependency checking functionality."""
        print("Testing Haio Drive Client dependency checker...")
        print(f"Platform: {platform.system()}")
        print(f"Architecture: {platform.machine()}")
        print()
        
        # Create RcloneManager instance
        manager = RcloneManager()
        
        # Check dependencies
        print("Checking dependencies...")
        issues = manager.check_dependencies()
        
        if issues:
            print(f"Found {len(issues)} dependency issues:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("✓ All dependencies are satisfied!")
        
        print()
        
        # Test Qt dependency checking specifically on Linux
        if platform.system() == "Linux":
            print("Checking Qt dependencies specifically...")
            qt_issues = manager._check_qt_dependencies()
            
            if qt_issues:
                print(f"Found {len(qt_issues)} Qt dependency issues:")
                for i, issue in enumerate(qt_issues, 1):
                    print(f"  {i}. {issue}")
            else:
                print("✓ All Qt dependencies are satisfied!")
        
        return len(issues) == 0
    
    if __name__ == "__main__":
        success = test_dependency_check()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the client directory")
    sys.exit(1)
except Exception as e:
    print(f"Error during testing: {e}")
    sys.exit(1)