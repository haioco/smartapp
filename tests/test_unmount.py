#!/usr/bin/env python3
"""
Test script for unmount functionality
"""
import os
import tempfile
import subprocess
from main_new import RcloneManager

def test_unmount():
    """Test the unmount functionality with a temporary directory."""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_mount_point = os.path.join(temp_dir, "test_mount")
        os.makedirs(test_mount_point, exist_ok=True)
        
        print(f"Testing unmount with directory: {test_mount_point}")
        
        # Create RcloneManager instance
        rclone_manager = RcloneManager()
        
        # Test unmounting a non-mounted directory
        print("Testing unmount of non-mounted directory...")
        result = rclone_manager.unmount_bucket(test_mount_point)
        print(f"Result: {result} (should be True for non-mounted directory)")
        
        # Test unmounting non-existent directory
        non_existent = os.path.join(temp_dir, "does_not_exist")
        print(f"\nTesting unmount of non-existent directory: {non_existent}")
        result = rclone_manager.unmount_bucket(non_existent)
        print(f"Result: {result} (should be True for non-existent directory)")
        
        print("\nUnmount test completed!")

if __name__ == "__main__":
    test_unmount()
