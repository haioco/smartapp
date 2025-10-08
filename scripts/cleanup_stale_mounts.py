#!/usr/bin/env python3
"""
Haio Smart App - Stale Mount Cleanup Utility

This utility helps clean up stale/broken mount points that were left behind
by crashed rclone processes or improperly terminated mounts.

Common errors this fixes:
- "Transport endpoint is not connected"
- "[Errno 17] File exists" when trying to mount
- Mount points that exist but can't be accessed

Usage:
    python cleanup_stale_mounts.py                  # Interactive mode
    python cleanup_stale_mounts.py --auto           # Auto cleanup
    python cleanup_stale_mounts.py --mount-point /path/to/mount
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def is_stale_mount(mount_point: str) -> tuple[bool, str]:
    """Check if mount point is stale/broken."""
    # First try to access it - this will fail for stale mounts
    try:
        # Try to list the mount point
        os.listdir(mount_point)
        return False, "Mount point is accessible (not stale)"
    except OSError as e:
        error_msg = str(e).lower()
        if 'transport endpoint is not connected' in error_msg:
            return True, f"Stale mount detected: {e}"
        if 'not a directory' in error_msg:
            return True, f"Broken mount point: {e}"
        if 'no such file or directory' in error_msg:
            return False, "Mount point does not exist"
        return True, f"Mount point has access error: {e}"
    except Exception as e:
        return False, f"Unknown error: {e}"


def cleanup_stale_mount(mount_point: str, force: bool = False) -> tuple[bool, str]:
    """Clean up a stale mount point."""
    print(f"\n🔧 Cleaning up: {mount_point}")
    
    # Check if it's actually stale
    is_stale, reason = is_stale_mount(mount_point)
    if not is_stale and not force:
        return False, f"❌ Not a stale mount: {reason}"
    
    if is_stale:
        print(f"   Reason: {reason}")
    
    # Try to unmount first
    print(f"   Step 1: Attempting to unmount...")
    unmount_commands = [
        ['fusermount', '-uz', mount_point],  # -z for lazy unmount
        ['fusermount3', '-uz', mount_point],
        ['umount', '-l', mount_point],  # lazy unmount
        ['umount', mount_point],
    ]
    
    unmounted = False
    for cmd in unmount_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   ✅ Unmounted successfully with: {' '.join(cmd)}")
                unmounted = True
                break
            else:
                print(f"   ⚠️  {cmd[0]} failed: {result.stderr.strip()}")
        except FileNotFoundError:
            pass  # Command not available
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  {cmd[0]} timed out")
        except Exception as e:
            print(f"   ⚠️  {cmd[0]} error: {e}")
    
    # Remove the mount point file/directory
    print(f"   Step 2: Removing mount point...")
    try:
        if os.path.isdir(mount_point):
            # Check if it's empty now
            if not os.listdir(mount_point):
                os.rmdir(mount_point)
                print(f"   ✅ Removed empty directory")
            else:
                return False, "   ❌ Directory is not empty after unmount"
        else:
            # It's a file (broken mount point)
            os.remove(mount_point)
            print(f"   ✅ Removed stale mount point file")
        
        return True, "✅ Successfully cleaned up stale mount"
    
    except Exception as e:
        return False, f"❌ Failed to remove mount point: {e}"


def find_haio_mount_points() -> list[str]:
    """Find all Haio mount points in the user's home directory."""
    home = Path.home()
    mount_points = []
    
    # Look for directories matching: ~/haio-{username}-{bucket}
    for item in home.glob("haio-*"):
        try:
            # Try to check if it's a directory or exists
            # This can fail for stale mounts
            if item.is_dir() or item.exists():
                mount_points.append(str(item))
        except OSError:
            # Stale mount - can't check status, but we want to include it
            mount_points.append(str(item))
    
    return mount_points


def main():
    parser = argparse.ArgumentParser(
        description="Clean up stale Haio mount points",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode - scan and prompt for each mount
  python cleanup_stale_mounts.py
  
  # Auto cleanup all stale mounts
  python cleanup_stale_mounts.py --auto
  
  # Clean specific mount point
  python cleanup_stale_mounts.py --mount-point /home/user/haio-user-bucket
  
  # Force cleanup even if not detected as stale
  python cleanup_stale_mounts.py --mount-point /path --force
        """
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Automatically clean up all detected stale mounts without prompting'
    )
    
    parser.add_argument(
        '--mount-point',
        type=str,
        help='Clean up a specific mount point'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force cleanup even if mount point is not detected as stale'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Haio Smart App - Stale Mount Cleanup Utility")
    print("=" * 60)
    
    # Single mount point mode
    if args.mount_point:
        success, message = cleanup_stale_mount(args.mount_point, force=args.force)
        print(f"\n{message}")
        return 0 if success else 1
    
    # Scan for Haio mount points
    print("\n🔍 Scanning for Haio mount points...")
    mount_points = find_haio_mount_points()
    
    if not mount_points:
        print("✅ No Haio mount points found in home directory")
        return 0
    
    print(f"📁 Found {len(mount_points)} mount point(s):\n")
    
    # Check each mount point
    stale_mounts = []
    for mp in mount_points:
        is_stale, reason = is_stale_mount(mp)
        status = "🔴 STALE" if is_stale else "🟢 OK"
        print(f"{status}  {mp}")
        if is_stale:
            print(f"         └─ {reason}")
            stale_mounts.append(mp)
    
    if not stale_mounts:
        print("\n✅ All mount points are healthy!")
        return 0
    
    print(f"\n⚠️  Found {len(stale_mounts)} stale mount(s)")
    
    # Auto mode or interactive mode
    if args.auto:
        print("\n🤖 Auto cleanup mode enabled")
        for mp in stale_mounts:
            cleanup_stale_mount(mp)
    else:
        print("\n💡 Run with --auto to clean up automatically")
        print("   Or clean up individually with --mount-point <path>")
        
        # Ask user if they want to clean up
        try:
            response = input("\nClean up all stale mounts now? [y/N]: ").strip().lower()
            if response in ['y', 'yes']:
                for mp in stale_mounts:
                    cleanup_stale_mount(mp)
            else:
                print("❌ Cleanup cancelled")
                return 1
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Cleanup cancelled")
            return 1
    
    print("\n" + "=" * 60)
    print("✅ Cleanup complete!")
    print("=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
