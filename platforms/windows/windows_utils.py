#!/usr/bin/env python3
"""
Windows-specific utilities for the HAIO S3 Drive Mounter
"""

import platform
import subprocess
import os


def is_windows_dark_mode():
    """
    Detect if Windows is in dark mode
    Returns: True if dark mode is enabled, False otherwise
    """
    if platform.system() != "Windows":
        return False
    
    try:
        import winreg
        
        # Check system theme
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        
        # 0 = Dark mode, 1 = Light mode
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        
        return value == 0
    except Exception:
        return False


def get_windows_mount_drive():
    """
    Get next available drive letter for Windows mounting
    Returns: Drive letter like 'Z:' or None if no drives available
    """
    if platform.system() != "Windows":
        return None
    
    import string
    
    # Get all available drive letters (Z to A, descending)
    available_drives = []
    for letter in reversed(string.ascii_uppercase):
        drive = f"{letter}:"
        if not os.path.exists(drive):
            available_drives.append(drive)
    
    return available_drives[0] if available_drives else None


def mount_windows_drive(rclone_remote, drive_letter, cache_dir):
    """
    Mount rclone remote as Windows drive
    
    Args:
        rclone_remote: Remote path (e.g., 'myconfig:mybucket')
        drive_letter: Drive letter to mount to (e.g., 'Z:')
        cache_dir: Cache directory path
    
    Returns:
        (success, message, process)
    """
    if platform.system() != "Windows":
        return False, "Not on Windows", None
    
    try:
        cmd = [
            'rclone', 'mount',
            '--swift-no-chunk',
            '--dir-cache-time', '10s',
            '--poll-interval', '1m',
            '--vfs-cache-mode', 'full',
            '--vfs-cache-max-age', '24h',
            '--vfs-write-back', '10s',
            '--vfs-read-wait', '20ms',
            '--no-modtime',
            '--buffer-size', '32M',
            '--attr-timeout', '1m',
            '--cache-dir', cache_dir,
            '--network-mode',  # Windows specific for network drive
            rclone_remote,
            drive_letter
        ]
        
        # Start rclone as background process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        
        return True, f"Mounting to {drive_letter}", process
    
    except Exception as e:
        return False, f"Mount failed: {str(e)}", None


def unmount_windows_drive(drive_letter):
    """
    Unmount Windows drive
    
    Args:
        drive_letter: Drive letter to unmount (e.g., 'Z:')
    
    Returns:
        (success, message)
    """
    if platform.system() != "Windows":
        return False, "Not on Windows"
    
    try:
        # Kill rclone process for this drive
        result = subprocess.run(
            ['taskkill', '/F', '/IM', 'rclone.exe'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True, "Unmount successful"
        else:
            return False, f"Unmount failed: {result.stderr}"
    
    except Exception as e:
        return False, f"Unmount error: {str(e)}"


def create_windows_startup_task(task_name, rclone_remote, drive_letter, cache_dir):
    """
    Create Windows Task Scheduler task for auto-mount at startup
    
    Args:
        task_name: Name for the scheduled task
        rclone_remote: Remote path (e.g., 'myconfig:mybucket')
        drive_letter: Drive letter to mount to
        cache_dir: Cache directory path
    
    Returns:
        (success, message)
    """
    if platform.system() != "Windows":
        return False, "Not on Windows"
    
    try:
        # Get rclone path
        rclone_path = "rclone.exe"
        
        # Create XML for task scheduler
        xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>HAIO Drive Auto-Mount</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions>
    <Exec>
      <Command>{rclone_path}</Command>
      <Arguments>mount --swift-no-chunk --vfs-cache-mode full --cache-dir "{cache_dir}" --network-mode "{rclone_remote}" {drive_letter}</Arguments>
    </Exec>
  </Actions>
</Task>
"""
        
        # Write XML to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_file = f.name
        
        # Create task using schtasks
        result = subprocess.run(
            ['schtasks', '/Create', '/TN', task_name, '/XML', xml_file, '/F'],
            capture_output=True,
            text=True
        )
        
        # Clean up temp file
        try:
            os.unlink(xml_file)
        except:
            pass
        
        if result.returncode == 0:
            return True, f"Startup task created: {task_name}"
        else:
            return False, f"Failed to create task: {result.stderr}"
    
    except Exception as e:
        return False, f"Error creating startup task: {str(e)}"


def remove_windows_startup_task(task_name):
    """
    Remove Windows Task Scheduler task
    
    Args:
        task_name: Name of the scheduled task to remove
    
    Returns:
        (success, message)
    """
    if platform.system() != "Windows":
        return False, "Not on Windows"
    
    try:
        result = subprocess.run(
            ['schtasks', '/Delete', '/TN', task_name, '/F'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True, f"Startup task removed: {task_name}"
        else:
            return False, f"Failed to remove task: {result.stderr}"
    
    except Exception as e:
        return False, f"Error removing startup task: {str(e)}"


def check_winfsp_installed():
    """
    Check if WinFsp is installed (required for rclone mount on Windows)
    
    Returns:
        (is_installed, version_or_message)
    """
    if platform.system() != "Windows":
        return False, "Not on Windows"
    
    try:
        import winreg
        
        # Check WinFsp registry key
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WinFsp"
        )
        
        version, _ = winreg.QueryValueEx(key, "Version")
        winreg.CloseKey(key)
        
        return True, f"WinFsp version {version}"
    
    except Exception:
        return False, "WinFsp not installed. Please install from https://winfsp.dev/"


def install_winfsp_prompt():
    """
    Show installation instructions for WinFsp
    
    Returns:
        Installation message
    """
    return """
WinFsp is required for mounting drives on Windows.

Please install WinFsp:
1. Download from: https://winfsp.dev/rel/
2. Install the latest stable version
3. Restart this application

WinFsp is a free, open-source Windows File System Proxy.
It allows rclone to mount cloud storage as a Windows drive letter.
"""
