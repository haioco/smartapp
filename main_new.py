import sys
import os
import json
import subprocess
import platform
import threading
import time
import configparser
import requests
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLineEdit, QLabel, QMessageBox,
    QTextEdit, QProgressBar, QGroupBox, QFrame, QCheckBox,
    QScrollArea, QStackedWidget, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem,
    QSizePolicy, QDialog, QDialogButtonBox, QFormLayout, QStatusBar,
    QListWidget, QListWidgetItem, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize, QMetaObject, Q_ARG
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QLinearGradient, QBrush, QAction, QPainterPath

class ApiError(Exception):
    pass


class PasswordDialog(QDialog):
    """GUI dialog for password input with sudo operations."""
    
    def __init__(self, parent=None, message="Enter your system password:"):
        super().__init__(parent)
        self.setWindowTitle("System Password Required")
        self.setModal(True)
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout(self)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # Password input
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("System password")
        layout.addWidget(self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)
        
        # Set default button and focus
        self.ok_button.setDefault(True)
        self.password_input.setFocus()
        
    def get_password(self):
        """Get the entered password."""
        return self.password_input.text()


class ApiClient:
    """Simplified API client for authentication and bucket operations."""
    
    def __init__(self, base_url: str = "https://drive.haio.ir"):
        self.base_url = base_url.rstrip('/')
        self.auth_url = f"{base_url}/auth/v1.0"
        self.api_url = f"{base_url}/v1"
        self.token = None
        self.storage_url = None
        self.account = None
        self.username = None
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user and get token."""
        try:
            headers = {
                'X-Storage-User': f'{username}:{username}',  # account:username format
                'X-Storage-Pass': password,
            }
            
            resp = requests.get(self.auth_url, headers=headers, timeout=10)
            
            if resp.status_code not in (200, 204):
                return False
                
            self.token = resp.headers.get('X-Auth-Token')
            self.storage_url = resp.headers.get('X-Storage-Url')
            self.account = username
            self.username = username
            
            return self.token is not None
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def list_containers(self) -> List[Dict]:
        """List user's containers (buckets)."""
        if not self.token or not self.storage_url:
            return []
        
        try:
            headers = {'X-Auth-Token': self.token}
            resp = requests.get(f"{self.storage_url}?format=json", headers=headers, timeout=10)
            
            if resp.status_code == 200:
                return resp.json()
            return []
            
        except Exception as e:
            print(f"Error listing containers: {e}")
            return []


class RcloneManager:
    """Manages rclone configuration and mounting operations."""
    
    def __init__(self):
        self.home_dir = os.path.expanduser("~")
        
        # Platform-specific paths
        if platform.system() == "Windows":
            self.config_dir = os.path.join(self.home_dir, "AppData", "Roaming", "rclone")
            self.cache_dir = os.path.join(self.home_dir, "AppData", "Local", "rclone", "cache")
            self.service_dir = None  # No systemd on Windows
            self.rclone_executable = self._find_rclone_executable()
        else:  # Linux/Unix
            self.config_dir = os.path.join(self.home_dir, ".config", "rclone")
            self.cache_dir = os.path.join(self.home_dir, ".cache", "rclone")
            self.service_dir = "/etc/systemd/system"
            self.rclone_executable = self._find_rclone_executable()
        
        self.config_path = os.path.join(self.config_dir, "rclone.conf")
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _find_rclone_executable(self):
        """Find rclone executable with priority to bundled version."""
        if platform.system() == "Windows":
            # Check for bundled rclone first (in same directory as executable)
            possible_paths = [
                os.path.join(os.path.dirname(sys.executable), "rclone.exe"),  # Bundled with app
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "rclone.exe"),  # Same dir as script
                "rclone.exe",  # If in PATH
                "C:\\Program Files\\rclone\\rclone.exe",
                "C:\\Program Files (x86)\\rclone\\rclone.exe",
                os.path.join(self.home_dir, "rclone", "rclone.exe"),
            ]
        else:  # Linux/Unix
            possible_paths = [
                os.path.join(os.path.dirname(sys.executable), "rclone"),  # Bundled with app
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "rclone"),  # Same dir as script
                "rclone",  # If in PATH
                "/usr/local/bin/rclone",
                "/usr/bin/rclone",
                os.path.join(self.home_dir, ".local/bin/rclone"),
            ]
        
        for path in possible_paths:
            if os.path.isfile(path):
                if platform.system() != "Windows":
                    # Make sure it's executable on Unix systems
                    try:
                        os.chmod(path, 0o755)
                    except:
                        pass
                return path
            elif path.endswith(("rclone.exe", "rclone")) and self._check_path_executable(path):
                return path
        
        # Fallback
        return "rclone.exe" if platform.system() == "Windows" else "rclone"
    
    def _check_path_executable(self, executable):
        """Check if executable is available in PATH."""
        try:
            subprocess.run([executable, "--version"], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def check_dependencies(self):
        """Check if required dependencies are available."""
        issues = []
        
        # Check rclone
        try:
            result = subprocess.run([self.rclone_executable, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                issues.append(f"rclone is not working properly")
        except FileNotFoundError:
            issues.append("rclone is not installed or not found in PATH")
        except subprocess.TimeoutExpired:
            issues.append("rclone is not responding")
        except Exception as e:
            issues.append(f"Error checking rclone: {e}")
        
        # Check FUSE on Linux
        if platform.system() == "Linux":
            if not os.path.exists("/usr/bin/fusermount") and not os.path.exists("/bin/fusermount"):
                issues.append("FUSE is not installed (install with: sudo apt-get install fuse)")
        
        # Check WinFsp on Windows with better detection
        elif platform.system() == "Windows":
            winfsp_installed = self._check_winfsp_installation()
            if not winfsp_installed:
                # Check if we have bundled WinFsp installer
                bundled_installer = self._find_bundled_winfsp_installer()
                if bundled_installer:
                    issues.append(f"WinFsp needs to be installed. Installer available at: {bundled_installer}")
                else:
                    issues.append("WinFsp is not installed (download from: https://github.com/billziss-gh/winfsp/releases)")
        
        return issues
    
    def _check_winfsp_installation(self):
        """Check if WinFsp is properly installed on Windows."""
        if platform.system() != "Windows":
            return True
            
        # Check multiple possible WinFsp installation paths
        winfsp_paths = [
            r"C:\Program Files\WinFsp\bin\launchctl-x64.exe",
            r"C:\Program Files (x86)\WinFsp\bin\launchctl-x64.exe",
            r"C:\Program Files\WinFsp\bin\winfsp-x64.dll",
            r"C:\Program Files (x86)\WinFsp\bin\winfsp-x64.dll",
            # Check system driver
            r"C:\Windows\System32\drivers\winfsp.sys"
        ]
        
        # Check if any WinFsp files exist
        winfsp_found = any(os.path.exists(path) for path in winfsp_paths)
        
        if winfsp_found:
            # Also try to verify WinFsp service is available
            try:
                result = subprocess.run(['sc', 'query', 'WinFsp'], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            except:
                # If service check fails, but files exist, assume it's installed
                return True
        
        return False
    
    def _find_bundled_winfsp_installer(self):
        """Find bundled WinFsp installer."""
        if platform.system() != "Windows":
            return None
            
        possible_locations = [
            os.path.join(os.path.dirname(sys.executable), "winfsp-installer.msi"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "winfsp-installer.msi"),
            "winfsp-installer.msi"
        ]
        
        for location in possible_locations:
            if os.path.exists(location):
                return location
        
        return None
    
    def install_winfsp(self, parent_widget=None):
        """Install WinFsp using bundled installer."""
        if platform.system() != "Windows":
            return False
            
        installer_path = self._find_bundled_winfsp_installer()
        if not installer_path:
            return False
            
        try:
            from PyQt6.QtWidgets import QMessageBox
            
            if parent_widget:
                reply = QMessageBox.question(
                    parent_widget,
                    "Install WinFsp",
                    "WinFsp is required for mounting cloud storage on Windows.\n\n"
                    "Do you want to install it now? This will require administrator privileges.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return False
            
            # Run the MSI installer with elevated privileges
            result = subprocess.run([
                "msiexec", "/i", installer_path, "/quiet", "/norestart"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                if parent_widget:
                    QMessageBox.information(
                        parent_widget,
                        "Installation Complete",
                        "WinFsp has been installed successfully!\n\n"
                        "Please restart the application to use the mounting features."
                    )
                return True
            else:
                if parent_widget:
                    QMessageBox.warning(
                        parent_widget,
                        "Installation Failed",
                        f"Failed to install WinFsp.\n\n"
                        f"Error: {result.stderr}\n\n"
                        "You may need to run the installer manually with administrator privileges."
                    )
                return False
                
        except Exception as e:
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Installation Error",
                    f"An error occurred while installing WinFsp:\n\n{str(e)}"
                )
            return False
    
    def setup_rclone_config(self, username: str, password: str):
        """Setup rclone configuration for the user."""
        config = configparser.ConfigParser()
        
        # Read existing config if it exists
        if os.path.exists(self.config_path):
            config.read(self.config_path)
        
        # Add or update the user's config section
        section_name = f"haio_{username}"
        if not config.has_section(section_name):
            config.add_section(section_name)
        
        config.set(section_name, 'type', 'swift')
        config.set(section_name, 'user', f'{username}:{username}')
        config.set(section_name, 'key', password)
        config.set(section_name, 'auth', 'https://drive.haio.ir/auth/v1.0')
        
        # Write config
        with open(self.config_path, 'w') as f:
            config.write(f)
    
    def mount_bucket(self, username: str, bucket_name: str, mount_point: str) -> bool:
        """Mount a bucket using rclone."""
        try:
            # Create mount point
            os.makedirs(mount_point, exist_ok=True)
            
            # Check if already mounted
            if self.is_mounted(mount_point):
                print(f"Bucket {bucket_name} is already mounted at {mount_point}")
                return True
            
            # Check dependencies before mounting
            if platform.system() == "Windows":
                if not self._check_winfsp_installation():
                    print("ERROR: WinFsp is not installed. Please install WinFsp before mounting.")
                    return False
            
            # Setup rclone mount command
            config_name = f"haio_{username}"
            cmd = [
                self.rclone_executable, 'mount',
                '--daemon',
                '--allow-non-empty',
                '--dir-cache-time', '10s',
                '--poll-interval', '1m',
                '--vfs-cache-mode', 'full',
                '--vfs-cache-max-age', '24h',
                '--vfs-write-back', '10s',
                '--vfs-read-wait', '20ms',
                '--buffer-size', '32M',
                '--attr-timeout', '1m',
                '--cache-dir', self.cache_dir,
                '--config', self.config_path,
                f'{config_name}:{bucket_name}',
                mount_point
            ]
            
            # Add Windows-specific options
            if platform.system() == "Windows":
                cmd.extend([
                    '--network-mode',  # Use network mode on Windows
                    '--volname', f'Haio-{bucket_name}'  # Set volume name
                ])
            
            print(f"Mounting {bucket_name} with command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"Mount command completed successfully for {bucket_name}")
                # Wait a moment and check if mount is actually active
                import time
                time.sleep(2)
                if self.is_mounted(mount_point):
                    print(f"Mount verification successful for {bucket_name}")
                    return True
                else:
                    print(f"Mount command succeeded but mount point is not active for {bucket_name}")
                    print(f"STDOUT: {result.stdout}")
                    print(f"STDERR: {result.stderr}")
                    return False
            else:
                print(f"Mount command failed for {bucket_name}")
                print(f"Return code: {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False
            
        except subprocess.TimeoutExpired:
            print(f"Mount command timed out for {bucket_name}")
            return False
        except Exception as e:
            print(f"Error mounting {bucket_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unmount_bucket(self, mount_point: str) -> bool:
        """Unmount a bucket."""
        try:
            if not os.path.exists(mount_point):
                print(f"Mount point {mount_point} does not exist")
                return True  # Consider it unmounted if it doesn't exist
            
            if not self.is_mounted(mount_point):
                print(f"Mount point {mount_point} is not mounted")
                return True
            
            print(f"Attempting to unmount {mount_point}")
            
            # Try different unmount commands based on platform
            if platform.system() == "Linux":
                # Try fusermount first (preferred for FUSE), then umount
                commands = [
                    ['fusermount', '-u', mount_point],
                    ['fusermount3', '-u', mount_point],
                    ['umount', mount_point]
                ]
            else:  # Windows
                # For Windows, we need to kill the rclone process
                commands = [['umount', mount_point]]
            
            for cmd in commands:
                try:
                    print(f"Trying command: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print(f"Successfully unmounted {mount_point}")
                        return True
                    else:
                        print(f"Command failed with code {result.returncode}: {result.stderr}")
                except FileNotFoundError:
                    print(f"Command not found: {cmd[0]}")
                    continue
                except subprocess.TimeoutExpired:
                    print(f"Command timed out: {' '.join(cmd)}")
                    continue
            
            # If unmount failed due to busy device, try additional strategies
            if platform.system() == "Linux":
                return self._handle_busy_unmount(mount_point)
            
            print(f"All unmount attempts failed for {mount_point}")
            return False
            
        except Exception as e:
            print(f"Error unmounting {mount_point}: {e}")
            return False
    
    def _handle_busy_unmount(self, mount_point: str) -> bool:
        """Handle unmount when device is busy."""
        print(f"Mount point {mount_point} is busy, trying additional strategies...")
        
        # Check what processes are using the mount point
        try:
            print("Checking for processes using the mount point...")
            result = subprocess.run(['lsof', '+D', mount_point], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                print("Processes using the mount point:")
                print(result.stdout)
                
                # Try to kill file manager processes that might be accessing the mount
                self._kill_file_managers(mount_point)
                
                # Wait a moment for processes to exit
                time.sleep(2)
                
                # Try unmount again
                for cmd in [['fusermount', '-u', mount_point], ['umount', mount_point]]:
                    try:
                        print(f"Retrying: {' '.join(cmd)}")
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            print(f"Successfully unmounted {mount_point} after killing processes")
                            return True
                    except:
                        continue
                        
        except FileNotFoundError:
            print("lsof not available, skipping process check")
        except Exception as e:
            print(f"Error checking processes: {e}")
        
        # Try lazy unmount as last resort
        try:
            print("Trying lazy unmount...")
            result = subprocess.run(['umount', '-l', mount_point], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"Lazy unmounted {mount_point}")
                return True
            else:
                print(f"Lazy unmount failed: {result.stderr}")
        except Exception as e:
            print(f"Lazy unmount error: {e}")
        
        print(f"All unmount strategies failed for {mount_point}")
        return False
    
    def _kill_file_managers(self, mount_point: str):
        """Kill common file manager processes that might be accessing the mount."""
        file_managers = ['nautilus', 'thunar', 'dolphin', 'nemo', 'pcmanfm']
        
        for fm in file_managers:
            try:
                # Check if the file manager is running
                result = subprocess.run(['pgrep', fm], capture_output=True, timeout=3)
                if result.returncode == 0:
                    print(f"Killing {fm} file manager...")
                    subprocess.run(['pkill', fm], timeout=3)
            except:
                continue
    
    def is_mounted(self, mount_point: str) -> bool:
        """Check if a mount point is currently mounted."""
        try:
            result = subprocess.run(['mountpoint', '-q', mount_point], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def create_systemd_service(self, username: str, bucket_name: str, mount_point: str, parent_widget=None) -> bool:
        """Create a systemd service for persistent mounting. Linux only."""
        if platform.system() != "Linux":
            if parent_widget:
                QMessageBox.information(parent_widget, "Not Supported", 
                                      "Auto-mount at boot is only supported on Linux systems.")
            return False
            
        try:
            service_name = f"haio-{username}-{bucket_name}.service"
            service_path = f"{self.service_dir}/{service_name}"
            config_name = f"haio_{username}"
            
            service_content = f"""[Unit]
Description=Haio Drive Mount - {bucket_name}
After=network-online.target

[Service]
Environment=DrivePathDirectory="{mount_point}"
Environment=CachePathDirectory="{self.cache_dir}"
Environment=RcloneConfig="{self.config_path}"
Environment=ConfigName="{config_name}"
Environment=ContainerName="{bucket_name}"

Type=simple
ExecStart={self.rclone_executable} mount \\
        --allow-non-empty \\
        --dir-cache-time 10s \\
        --poll-interval 1m \\
        --vfs-cache-mode full \\
        --vfs-cache-max-age 24h \\
        --vfs-write-back 10s \\
        --vfs-read-wait 20ms \\
        --buffer-size 32M \\
        --attr-timeout 1m \\
        --cache-dir "${{CachePathDirectory}}" \\
        --config "${{RcloneConfig}}" \\
        "${{ConfigName}}:${{ContainerName}}" "${{DrivePathDirectory}}"
ExecStop=/bin/bash -c 'fusermount -u "${{DrivePathDirectory}}" || umount -l "${{DrivePathDirectory}}"'
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
"""
            
            # Ask for password using GUI
            if parent_widget:
                password_dialog = PasswordDialog(
                    parent_widget, 
                    f"System password required to create auto-mount service for '{bucket_name}'.\n"
                    "This will create a systemd service that automatically mounts your bucket at boot."
                )
                
                if password_dialog.exec() != QDialog.DialogCode.Accepted:
                    return False
                    
                password = password_dialog.get_password()
                if not password:
                    return False
            else:
                # Fallback - should not happen in GUI app
                return False
            
            # Write service file to temp location first
            temp_file = f"/tmp/{service_name}"
            with open(temp_file, 'w') as f:
                f.write(service_content)
            
            # Move to systemd directory with sudo using GUI password
            commands = [
                f'echo "{password}" | sudo -S mv "{temp_file}" "{service_path}"',
                f'echo "{password}" | sudo -S systemctl daemon-reload',
                f'echo "{password}" | sudo -S systemctl enable "{service_name}"'
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    # Clean up temp file if it still exists
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error creating systemd service: {e}")
            return False
    
    def remove_systemd_service(self, username: str, bucket_name: str, parent_widget=None) -> bool:
        """Remove systemd service for a bucket. Linux only."""
        if platform.system() != "Linux":
            return True  # Nothing to remove on non-Linux systems
            
        try:
            service_name = f"haio-{username}-{bucket_name}.service"
            
            # Ask for password using GUI
            if parent_widget:
                password_dialog = PasswordDialog(
                    parent_widget, 
                    f"System password required to remove auto-mount service for '{bucket_name}'."
                )
                
                if password_dialog.exec() != QDialog.DialogCode.Accepted:
                    return False
                    
                password = password_dialog.get_password()
                if not password:
                    return False
            else:
                # Fallback - should not happen in GUI app
                return False
            
            # Remove service with sudo using GUI password
            commands = [
                f'echo "{password}" | sudo -S systemctl disable "{service_name}"',
                f'echo "{password}" | sudo -S systemctl stop "{service_name}"',
                f'echo "{password}" | sudo -S rm -f "{self.service_dir}/{service_name}"',
                f'echo "{password}" | sudo -S systemctl daemon-reload'
            ]
            
            for cmd in commands:
                subprocess.run(cmd, shell=True, capture_output=True, text=True)
                # Continue even if some commands fail (service might not exist)
            
            return True
            
        except Exception as e:
            print(f"Error removing systemd service: {e}")
            return False

    def is_systemd_service_enabled(self, username: str, bucket_name: str) -> bool:
        """Check if systemd service exists and is enabled for auto-mount. Linux only."""
        if platform.system() != "Linux":
            return False
            
        try:
            service_name = f"haio-{username}-{bucket_name}.service"
            
            # Check if service file exists
            service_path = f"{self.service_dir}/{service_name}"
            if not os.path.exists(service_path):
                return False
            
            # Check if service is enabled
            result = subprocess.run(['systemctl', 'is-enabled', service_name], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and result.stdout.strip() == 'enabled'
            
        except Exception as e:
            print(f"Error checking systemd service: {e}")
            return False

    def create_windows_startup_task(self, username: str, bucket_name: str, mount_point: str, parent_widget=None) -> bool:
        """Create a Windows Task Scheduler task for auto-mount at startup."""
        if platform.system() != "Windows":
            return False
            
        try:
            task_name = f"HaioMount-{username}-{bucket_name}"
            
            # Get the current executable path
            if hasattr(sys, '_MEIPASS'):
                # Running as PyInstaller bundle
                exe_path = sys.executable
            else:
                # Running as script
                exe_path = os.path.abspath(__file__)
            
            # Create PowerShell command to create scheduled task
            ps_command = f"""
            $Action = New-ScheduledTaskAction -Execute '{exe_path}' -Argument '--auto-mount --username {username} --bucket {bucket_name} --mount-point "{mount_point}"'
            $Trigger = New-ScheduledTaskTrigger -AtStartup
            $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
            $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
            Register-ScheduledTask -TaskName '{task_name}' -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
            """
            
            # Execute PowerShell command
            result = subprocess.run(['powershell', '-Command', ps_command], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                if parent_widget:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        parent_widget, 
                        "Auto-mount Enabled", 
                        f"Auto-mount task created successfully for '{bucket_name}'.\n"
                        f"The bucket will be automatically mounted when Windows starts."
                    )
                return True
            else:
                print(f"Failed to create Windows startup task: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error creating Windows startup task: {e}")
            return False
    
    def remove_windows_startup_task(self, username: str, bucket_name: str, parent_widget=None) -> bool:
        """Remove Windows Task Scheduler task for auto-mount."""
        if platform.system() != "Windows":
            return True
            
        try:
            task_name = f"HaioMount-{username}-{bucket_name}"
            
            # Remove the scheduled task
            result = subprocess.run(['schtasks', '/Delete', '/TN', task_name, '/F'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                if parent_widget:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        parent_widget, 
                        "Auto-mount Disabled", 
                        f"Auto-mount task removed successfully for '{bucket_name}'."
                    )
                return True
            else:
                # Task might not exist, which is fine
                return True
                
        except Exception as e:
            print(f"Error removing Windows startup task: {e}")
            return False
    
    def is_windows_startup_task_enabled(self, username: str, bucket_name: str) -> bool:
        """Check if Windows Task Scheduler task exists for auto-mount."""
        if platform.system() != "Windows":
            return False
            
        try:
            task_name = f"HaioMount-{username}-{bucket_name}"
            
            # Check if task exists
            result = subprocess.run(['schtasks', '/Query', '/TN', task_name], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error checking Windows startup task: {e}")
            return False

    def create_auto_mount_service(self, username: str, bucket_name: str, mount_point: str, parent_widget=None) -> bool:
        """Create auto-mount service for the current platform."""
        if platform.system() == "Linux":
            return self.create_systemd_service(username, bucket_name, mount_point, parent_widget)
        elif platform.system() == "Windows":
            return self.create_windows_startup_task(username, bucket_name, mount_point, parent_widget)
        else:
            if parent_widget:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(parent_widget, "Not Supported", 
                                      "Auto-mount at boot is not supported on this operating system.")
            return False
    
    def remove_auto_mount_service(self, username: str, bucket_name: str, parent_widget=None) -> bool:
        """Remove auto-mount service for the current platform."""
        if platform.system() == "Linux":
            return self.remove_systemd_service(username, bucket_name, parent_widget)
        elif platform.system() == "Windows":
            return self.remove_windows_startup_task(username, bucket_name, parent_widget)
        else:
            return True
    
    def is_auto_mount_service_enabled(self, username: str, bucket_name: str) -> bool:
        """Check if auto-mount service is enabled for the current platform."""
        if platform.system() == "Linux":
            return self.is_systemd_service_enabled(username, bucket_name)
        elif platform.system() == "Windows":
            return self.is_windows_startup_task_enabled(username, bucket_name)
        else:
            return False

class TokenManager:
    """Manages authentication tokens persistently."""
    
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.config/haio-client")
        self.token_file = os.path.join(self.config_dir, "tokens.json")
        os.makedirs(self.config_dir, exist_ok=True)
    
    def save_token(self, username: str, token: str, password: str = None):
        """Save authentication token."""
        try:
            data = {}
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
            
            data[username] = {
                'token': token,
                'timestamp': time.time()
            }
            if password:
                data[username]['password'] = password  # Consider encryption in production
            
            with open(self.token_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving token: {e}")
    
    def load_token(self, username: str) -> Optional[Dict]:
        """Load saved token data."""
        try:
            if not os.path.exists(self.token_file):
                return None
            
            with open(self.token_file, 'r') as f:
                data = json.load(f)
            
            return data.get(username)
            
        except Exception as e:
            print(f"Error loading token: {e}")
            return None
    
    def clear_tokens(self):
        """Clear all saved tokens."""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
        except Exception as e:
            print(f"Error clearing tokens: {e}")


class AuthWorker(QThread):
    """Worker thread for authentication operations."""
    finished = pyqtSignal(bool, str)  # success, username
    
    def __init__(self, api_client, username, password):
        super().__init__()
        self.api_client = api_client
        self.username = username
        self.password = password
    
    def run(self):
        """Perform authentication in thread."""
        try:
            success = self.api_client.authenticate(self.username, self.password)
            self.finished.emit(success, self.username if success else "")
        except Exception as e:
            print(f"Authentication error in worker: {e}")
            self.finished.emit(False, "")


class BucketWorker(QThread):
    """Worker thread for loading buckets."""
    finished = pyqtSignal(list)  # buckets list
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
    
    def run(self):
        """Load buckets in thread."""
        try:
            buckets = self.api_client.list_containers()
            self.finished.emit(buckets)
        except Exception as e:
            print(f"Error loading buckets: {e}")
            self.finished.emit([])


class MountWorker(QThread):
    """Worker thread for mount/unmount operations."""
    
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, operation: str, rclone_manager: RcloneManager, **kwargs):
        super().__init__()
        self.operation = operation
        self.rclone_manager = rclone_manager
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.operation == 'mount':
                success = self.rclone_manager.mount_bucket(**self.kwargs)
                message = "Mounted successfully" if success else "Mount failed - check logs for details"
            elif self.operation == 'unmount':
                mount_point = self.kwargs['mount_point']
                success = self.rclone_manager.unmount_bucket(mount_point)
                if success:
                    message = "Unmounted successfully"
                else:
                    # Try to get more specific error information
                    if not os.path.exists(mount_point):
                        message = f"Mount point {mount_point} does not exist"
                    elif not self.rclone_manager.is_mounted(mount_point):
                        message = f"Mount point {mount_point} is not mounted"
                    else:
                        # Check if it's a "device busy" issue
                        try:
                            result = subprocess.run(['lsof', '+D', mount_point], 
                                                  capture_output=True, text=True, timeout=3)
                            if result.returncode == 0 and result.stdout.strip():
                                message = f"Cannot unmount {mount_point}: files are being accessed by applications. Close any file managers or applications using files in this location and try again."
                            else:
                                message = f"Failed to unmount {mount_point}. Try closing all applications and file managers."
                        except:
                            message = f"Failed to unmount {mount_point}. The mount point may be busy - close any applications accessing files in this location."
            else:
                success = False
                message = "Unknown operation"
            
            self.finished.emit(success, message)
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class BucketWidget(QFrame):
    """Custom widget for displaying bucket information with mount controls."""
    
    mount_requested = pyqtSignal(str, str)  # bucket_name, mount_point
    unmount_requested = pyqtSignal(str)     # mount_point
    auto_mount_changed = pyqtSignal(str, bool)  # bucket_name, enabled
    
    def __init__(self, bucket_info: Dict, username: str, rclone_manager: RcloneManager):
        super().__init__()
        self.bucket_info = bucket_info
        self.username = username
        self.rclone_manager = rclone_manager
        # Use user's home directory instead of /mnt/ to avoid permission issues
        user_home = os.path.expanduser("~")
        self.mount_point = f"{user_home}/haio-{username}-{bucket_info['name']}"
        self.is_mounted = False
        
        self.setup_ui()
        self.update_mount_status()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            BucketWidget {
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                background-color: white;
                margin: 5px;
            }
            BucketWidget:hover {
                border-color: #4CAF50;
                background-color: #f8fff8;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header with bucket name and size
        header_layout = QHBoxLayout()
        
        # Bucket name
        name_label = QLabel(self.bucket_info['name'])
        name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        
        # Size info
        size_text = self.format_size(self.bucket_info.get('bytes', 0))
        count_text = f"{self.bucket_info.get('count', 0)} objects"
        
        info_label = QLabel(f"{size_text} • {count_text}")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        header_layout.addWidget(info_label)
        
        layout.addLayout(header_layout)
        
        # Mount point info
        mount_info = QLabel(f"Mount point: {self.mount_point}")
        mount_info.setStyleSheet("color: #34495e; font-size: 11px;")
        layout.addWidget(mount_info)
        
        # Status and controls
        controls_layout = QHBoxLayout()
        
        # Mount status
        self.status_label = QLabel("Not mounted")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        # Mount/Unmount button
        self.mount_btn = QPushButton("Mount")
        self.mount_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.mount_btn.clicked.connect(self.toggle_mount)
        
        # Auto-mount checkbox
        self.auto_mount_cb = QCheckBox("Auto-mount at boot")
        self.auto_mount_cb.setStyleSheet("color: #34495e;")
        
        # Check current auto-mount status and set checkbox state
        is_auto_mount_enabled = self.rclone_manager.is_auto_mount_service_enabled(
            self.username, self.bucket_info['name'])
        self.auto_mount_cb.setChecked(is_auto_mount_enabled)
        
        self.auto_mount_cb.toggled.connect(self.on_auto_mount_changed)
        
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.auto_mount_cb)
        controls_layout.addWidget(self.mount_btn)
        
        layout.addLayout(controls_layout)
    
    def format_size(self, bytes_size: int) -> str:
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
    
    def update_mount_status(self):
        """Update the mount status display."""
        self.is_mounted = self.rclone_manager.is_mounted(self.mount_point)
        
        if self.is_mounted:
            self.status_label.setText("✓ Mounted")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.mount_btn.setText("Unmount")
            self.mount_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
        else:
            self.status_label.setText("Not mounted")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.mount_btn.setText("Mount")
            self.mount_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
    
    def toggle_mount(self):
        """Toggle mount status."""
        if self.is_mounted:
            self.unmount_requested.emit(self.mount_point)
        else:
            self.mount_requested.emit(self.bucket_info['name'], self.mount_point)
    
    def on_auto_mount_changed(self, checked: bool):
        """Handle auto-mount checkbox change."""
        self.auto_mount_changed.emit(self.bucket_info['name'], checked)


class LoginDialog(QDialog):
    """Beautiful login dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Haio Smart Solutions Login")
        self.setFixedSize(500, 550)  # Made larger to accommodate content properly
        self.setModal(True)
        
        # Remove default window decorations and add custom styling
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Variables for window dragging
        self.drag_position = None
        self.dragging = False
        
        # Store reference to parent for API client access
        self.parent_window = parent
        
        # Authentication worker
        self.auth_worker = None
        
        self.setup_ui()
        self.setup_styling()
        
        # Center the dialog on screen
        self.center_on_screen()
    
    def center_on_screen(self):
        """Center the dialog on the screen."""
        screen = QApplication.primaryScreen().geometry()
        dialog_geometry = self.geometry()
        x = (screen.width() - dialog_geometry.width()) // 2
        y = (screen.height() - dialog_geometry.height()) // 2
        self.move(x, y)
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.pos()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging."""
        if self.dragging and self.drag_position is not None:
            if event.buttons() == Qt.MouseButton.LeftButton:
                new_pos = event.globalPosition().toPoint() - self.drag_position
                self.move(new_pos)
                event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main frame
        self.main_frame = QFrame()
        self.main_frame.setObjectName("mainFrame")
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(40, 30, 40, 30)  # Balanced margins
        frame_layout.setSpacing(15)  # Reduced spacing for better fit
        
        # Logo/Title Section
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setSpacing(8)
        
        # Load and display the logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "haio-logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                # Scale the logo to appropriate size
                scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # Make logo background transparent
                logo_label.setStyleSheet("background: transparent; border: none;")
            else:
                # Fallback if image can't be loaded
                logo_label.setText("🔗")
                logo_label.setStyleSheet("font-size: 32px; background: transparent; color: #4CAF50;")
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            # Fallback icon
            logo_label.setText("🔗")
            logo_label.setStyleSheet("font-size: 32px; background: transparent; color: #4CAF50;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_layout.addWidget(logo_label)
        
        title = QLabel("Haio Smart Solutions")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        logo_layout.addWidget(title)
        
        frame_layout.addLayout(logo_layout)
        
        subtitle = QLabel("Connect to your cloud storage")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("subtitle")
        frame_layout.addWidget(subtitle)
        
        frame_layout.addSpacing(20)
        
        # Form section with clear separation
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(12)  # Consistent spacing between form elements
        form_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins
        
        # Username section
        username_label = QLabel("Username:")
        username_label.setObjectName("fieldLabel")
        username_label.setFixedHeight(20)  # Ensure label has enough height
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setObjectName("input")
        # Use minimum height so it scales with DPI/themes but never gets too small
        self.username_input.setMinimumHeight(40)
        self.username_input.setFixedHeight(40)  # Fixed height for consistency
        self.username_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addSpacing(15)  # Clear separation between sections
        
        # Password section
        password_label = QLabel("Password:")
        password_label.setObjectName("fieldLabel")
        password_label.setFixedHeight(20)  # Ensure label has enough height
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("input")
        self.password_input.setMinimumHeight(40)
        self.password_input.setFixedHeight(40)  # Fixed height for consistency
        self.password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(10)  # Space before checkbox
        
        # Remember me checkbox
        self.remember_cb = QCheckBox("Remember me")
        self.remember_cb.setObjectName("checkbox")
        self.remember_cb.setFixedHeight(25)  # Ensure checkbox has proper height
        form_layout.addWidget(self.remember_cb)
        
        # Error message label (initially hidden)
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()  # Initially hidden
        form_layout.addWidget(self.error_label)

        frame_layout.addWidget(form_widget)
        
        frame_layout.addSpacing(15)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.setFixedHeight(42)  # Consistent button height
        self.cancel_btn.clicked.connect(self.reject)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setFixedHeight(42)  # Consistent button height
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self.handle_login)  # Changed to handle_login method
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.login_btn)
        
        frame_layout.addLayout(button_layout)
        
        main_layout.addWidget(self.main_frame)
        
        # Connect Enter key to login
        self.password_input.returnPressed.connect(self.handle_login)  # Changed to handle_login method
    
    def handle_login(self):
        """Handle login button click with validation and authentication."""
        # Clear any previous error
        self.hide_error()
        
        # Get credentials
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Basic validation
        if not username:
            self.show_error("Please enter your username.")
            return
            
        if not password:
            self.show_error("Please enter your password.")
            return
        
        # Show loading state
        self.set_loading_state(True)
        
        # Start authentication in background thread
        if self.parent_window and hasattr(self.parent_window, 'api_client'):
            self.auth_worker = AuthWorker(self.parent_window.api_client, username, password)
            self.auth_worker.finished.connect(self.on_auth_finished)
            self.auth_worker.start()
        else:
            # Fallback: create temporary API client
            temp_api_client = ApiClient()
            self.auth_worker = AuthWorker(temp_api_client, username, password)
            self.auth_worker.finished.connect(self.on_auth_finished)
            self.auth_worker.start()
    
    def on_auth_finished(self, success: bool, username: str):
        """Handle authentication completion."""
        self.set_loading_state(False)
        
        if success:
            # Authentication successful - close dialog and accept
            self.accept()
        else:
            # Authentication failed - show error
            self.show_error("Invalid username or password. Please try again.")
    
    def set_loading_state(self, loading: bool):
        """Set the loading state of the login button."""
        if loading:
            self.login_btn.setText("Logging in...")
            self.login_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.username_input.setEnabled(False)
            self.password_input.setEnabled(False)
            self.remember_cb.setEnabled(False)
        else:
            self.login_btn.setText("Login")
            self.login_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.username_input.setEnabled(True)
            self.password_input.setEnabled(True)
            self.remember_cb.setEnabled(True)
    
    def show_error(self, message: str):
        """Show error message in the dialog."""
        self.error_label.setText(message)
        self.error_label.show()
        
        # Briefly highlight the error with animation
        self.error_label.setStyleSheet("""
            QLabel#errorLabel {
                color: #e74c3c;
                background-color: #fdf2f2;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
                padding: 8px;
                margin: 5px 0px;
                font-size: 12px;
            }
        """)
    
    def hide_error(self):
        """Hide error message."""
        self.error_label.hide()
        self.error_label.setText("")
    
    def setup_styling(self):
        self.setStyleSheet("""
            QDialog {
                background-color: transparent;
            }
            
            QFrame#mainFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
            
            QLabel#title {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;
                padding: 5px 0px;
            }
            
            QLabel#subtitle {
                font-size: 13px;
                color: #7f8c8d;
                padding: 2px 0px;
            }
            
            QLabel#fieldLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 13px;
                margin-bottom: 3px;
                padding: 3px 2px;
                background-color: transparent;
                min-height: 20px;
                max-height: 20px;
            }
            
            QLineEdit#input {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                background-color: #fafafa;
                color: #2c3e50;
                margin: 1px 0px;
                min-height: 20px;
                max-height: 40px;
            }
            
            QLineEdit#input:focus {
                border-color: #4CAF50;
                background-color: white;
                outline: none;
            }
            
            QCheckBox#checkbox {
                color: #34495e;
                font-size: 13px;
                margin-top: 3px;
                padding: 5px 0px;
                spacing: 8px;
                min-height: 25px;
                max-height: 25px;
            }
            
            QCheckBox#checkbox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                margin-right: 8px;
            }
            
            QCheckBox#checkbox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
                image: url(none);
            }
            
            QLabel#errorLabel {
                color: #e74c3c;
                background-color: #fdf2f2;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
                padding: 8px;
                margin: 5px 0px;
                font-size: 12px;
            }
            
            QPushButton#loginButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
                min-height: 42px;
                max-height: 42px;
            }
            
            QPushButton#loginButton:hover {
                background-color: #45a049;
            }
            
            QPushButton#loginButton:pressed {
                background-color: #3d8b40;
            }
            
            QPushButton#cancelButton {
                background-color: transparent;
                color: #7f8c8d;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                min-width: 100px;
                min-height: 42px;
                max-height: 42px;
            }
            
            QPushButton#cancelButton:hover {
                border-color: #bdc3c7;
                color: #34495e;
                background-color: #f8f9fa;
            }
            
            QPushButton#cancelButton:pressed {
                background-color: #e9ecef;
            }
        """)
    
    def get_credentials(self):
        """Get entered credentials."""
        return {
            'username': self.username_input.text().strip(),
            'password': self.password_input.text(),
            'remember': self.remember_cb.isChecked()
        }


class HaioDriveClient(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.api_client = ApiClient()
        self.rclone_manager = RcloneManager()
        self.token_manager = TokenManager()
        
        # Set application icon
        self.set_application_icon()
        
        # Check dependencies on startup
        self.check_dependencies()
        
        self.current_user = None
        self.buckets = []
        self.bucket_widgets = []
        
        # Store active workers to prevent premature destruction
        self.active_workers = []
        
        self.setup_ui()
        self.setup_styling()
        
        # Auto-login if credentials are saved
        # Don't show window initially - show only after login
        self.try_auto_login()
    
    def set_application_icon(self):
        """Set the application icon for window and taskbar."""
        try:
            # Try to load the logo file first
            logo_path = os.path.join(os.path.dirname(__file__), "haio-logo.png")
            
            if os.path.exists(logo_path):
                # Use the actual logo file
                icon = QIcon(logo_path)
            else:
                # Create a fallback icon programmatically
                icon = self.create_fallback_icon()
            
            # Set icon for the application and window
            self.setWindowIcon(icon)
            QApplication.instance().setWindowIcon(icon)
            
        except Exception as e:
            print(f"Error setting application icon: {e}")
            # Create a simple fallback icon
            self.setWindowIcon(self.create_simple_fallback_icon())
    
    def create_fallback_icon(self):
        """Create a fallback icon with Haio branding."""
        # Create a 64x64 icon
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient background
        gradient = QLinearGradient(0, 0, 64, 64)
        gradient.setColorAt(0, QColor("#4CAF50"))
        gradient.setColorAt(1, QColor("#45a049"))
        
        # Draw circle background
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        
        # Draw letter "H" in white
        painter.setPen(QColor(Qt.GlobalColor.white))
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "H")
        
        painter.end()
        return QIcon(pixmap)
    
    def create_simple_fallback_icon(self):
        """Create a very simple fallback icon."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#4CAF50"))
        return QIcon(pixmap)
    
    def check_dependencies(self):
        """Check if all required dependencies are available."""
        issues = self.rclone_manager.check_dependencies()
        
        if issues:
            # Check if WinFsp installation is available
            winfsp_installer_available = False
            winfsp_needs_install = False
            
            if platform.system() == "Windows":
                for issue in issues:
                    if "WinFsp" in issue and "Installer available" in issue:
                        winfsp_installer_available = True
                        winfsp_needs_install = True
                        break
                    elif "WinFsp" in issue:
                        winfsp_needs_install = True
            
            # If WinFsp installer is available, offer to install it automatically
            if winfsp_installer_available:
                reply = QMessageBox.question(
                    self,
                    "Install Required Dependencies",
                    "WinFsp is required for mounting cloud storage on Windows.\n\n"
                    "We have included the WinFsp installer with this application.\n"
                    "Would you like to install it now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    if self.rclone_manager.install_winfsp(self):
                        # Recheck dependencies after installation
                        remaining_issues = self.rclone_manager.check_dependencies()
                        if not remaining_issues:
                            return  # All dependencies resolved
                        issues = remaining_issues
                elif reply == QMessageBox.StandardButton.Cancel:
                    return
            
            # Show remaining issues
            issue_text = "\n".join([f"• {issue}" for issue in issues])
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Missing Dependencies")
            msg.setText("Some required dependencies are missing:")
            msg.setDetailedText(issue_text)
            
            if platform.system() == "Windows":
                if winfsp_needs_install and not winfsp_installer_available:
                    msg.setInformativeText(
                        "To use this application on Windows:\n"
                        "1. Download and install WinFsp from:\n"
                        "   https://github.com/billziss-gh/winfsp/releases\n"
                        "2. Restart the application\n\n"
                        "Note: rclone is already bundled with this application."
                    )
                else:
                    msg.setInformativeText(
                        "All required dependencies should be bundled with this application.\n"
                        "If you're seeing this message, please contact support."
                    )
            else:
                msg.setInformativeText(
                    "To use this application on Linux:\n"
                    "1. Install FUSE: sudo apt-get install fuse\n"
                    "2. Restart the application\n\n"
                    "Note: rclone is already bundled with this application."
                )
            
            msg.exec()
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Wait for all active workers to finish
        for worker in self.active_workers:
            if worker.isRunning():
                worker.wait(3000)  # Wait up to 3 seconds
        
        event.accept()
    
    def set_application_icon(self):
        """Set the application icon from logo file or create a default one."""
        # Try to load the Haio logo
        logo_path = os.path.join(os.path.dirname(__file__), "haio-logo.png")
        
        if os.path.exists(logo_path):
            # Use the existing logo file
            icon = QIcon(logo_path)
            self.setWindowIcon(icon)
            # Also set it as application icon for taskbar/dock
            QApplication.instance().setWindowIcon(icon)
        else:
            # Create a simple default icon if logo file doesn't exist
            self.create_default_icon()
    
    def create_default_icon(self):
        """Create a default icon with the Haio colors and branding."""
        # Create a 64x64 pixmap for the icon
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient background
        gradient = QLinearGradient(0, 0, 64, 64)
        gradient.setColorAt(0, QColor("#4CAF50"))  # Haio green
        gradient.setColorAt(1, QColor("#45a049"))  # Darker green
        
        # Draw circular background
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        
        # Draw "H" letter in white
        painter.setPen(QColor("white"))
        font = QFont("Arial", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "H")
        
        painter.end()
        
        # Set the icon
        icon = QIcon(pixmap)
        self.setWindowIcon(icon)
        QApplication.instance().setWindowIcon(icon)
    
    def setup_ui(self):
        self.setWindowTitle("Haio Smart Solutions Client")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Set application icon
        self.set_application_icon()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        self.create_header(main_layout)
        
        # Content area
        self.content_stack = QStackedWidget()
        
        # Loading page
        self.loading_page = self.create_loading_page()
        self.content_stack.addWidget(self.loading_page)
        
        # Buckets page
        self.buckets_page = self.create_buckets_page()
        self.content_stack.addWidget(self.buckets_page)
        
        main_layout.addWidget(self.content_stack)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_header(self, parent_layout):
        """Create the header section."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Logo and title
        title_layout = QHBoxLayout()
        title_layout.setSpacing(15)
        
        # Add logo with better handling
        logo_container = QFrame()
        logo_container.setFixedSize(64, 64)
        logo_container.setObjectName("logoContainer")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(8, 8, 8, 8)
        
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "haio-logo.png")
        
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                # Create a circular mask for the logo to remove white background
                masked_pixmap = self.create_circular_logo(pixmap, 48)
                logo_label.setPixmap(masked_pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                # Fallback to icon text
                logo_label.setText("🔗")
                logo_label.setStyleSheet("font-size: 24px; color: white;")
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            # Fallback to icon text with better styling
            logo_label.setText("H")
            logo_label.setStyleSheet("""
                font-size: 28px; 
                color: white; 
                font-weight: bold; 
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 24px;
                padding: 8px;
            """)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setFixedSize(48, 48)
        
        logo_layout.addWidget(logo_label)
        title_layout.addWidget(logo_container)
        
        # Title and user info with improved styling
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        app_title = QLabel("Haio Smart Solutions")
        app_title.setObjectName("appTitle")
        
        self.user_label = QLabel("Not logged in")
        self.user_label.setObjectName("userLabel")
        
        text_layout.addWidget(app_title)
        text_layout.addWidget(self.user_label)
        text_layout.addStretch()
        
        title_layout.addLayout(text_layout)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Action buttons with improved styling
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("headerButton")
        self.refresh_btn.clicked.connect(self.refresh_buckets)
        
        self.logout_btn = QPushButton("🚪 Logout")
        self.logout_btn.setObjectName("headerButton")
        self.logout_btn.clicked.connect(self.logout)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.logout_btn)
        
        header_layout.addWidget(button_container)
        
        parent_layout.addWidget(header)
    
    def create_circular_logo(self, pixmap, size):
        """Create a circular version of the logo to remove background."""
        # Scale pixmap to desired size
        scaled_pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
        
        # Create circular mask
        circular_pixmap = QPixmap(size, size)
        circular_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set circular clipping region
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        
        # Draw the scaled pixmap within the circular clip
        painter.drawPixmap(0, 0, scaled_pixmap)
        
        painter.end()
        return circular_pixmap
    
    def create_loading_page(self):
        """Create loading page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Loading message
        loading_label = QLabel("Loading your buckets...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setObjectName("loadingLabel")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setFixedWidth(300)
        
        layout.addWidget(loading_label)
        layout.addSpacing(20)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return page
    
    def create_buckets_page(self):
        """Create buckets page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Page title
        title = QLabel("Your Storage Buckets")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # Scroll area for buckets
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setObjectName("bucketsScrollArea")
        
        # Container for bucket widgets
        self.buckets_container = QWidget()
        self.buckets_layout = QVBoxLayout(self.buckets_container)
        self.buckets_layout.setSpacing(10)
        self.buckets_layout.addStretch()
        
        scroll_area.setWidget(self.buckets_container)
        layout.addWidget(scroll_area)
        
        return page
    
    def setup_styling(self):
        """Apply application styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            
            QFrame#header {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                border-bottom: 3px solid #3d8b40;
            }
            
            QFrame#logoContainer {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 32px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
            
            QLabel#appTitle {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            
            QLabel#userLabel {
                color: #e8f5e8;
                font-size: 13px;
                font-weight: 500;
            }
            
            QPushButton#headerButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 13px;
                margin: 0 2px;
                min-width: 90px;
            }
            
            QPushButton#headerButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
                border-color: rgba(255, 255, 255, 0.5);
            }
            
            QPushButton#headerButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            QLabel#loadingLabel {
                font-size: 16px;
                color: #34495e;
            }
            
            QLabel#pageTitle {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
            }
            
            QScrollArea#bucketsScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                text-align: center;
                background-color: #f8f9fa;
            }
            
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 6px;
            }
        """)
    
    def try_auto_login(self):
        """Try to automatically login with saved credentials."""
        # Start with loading page first
        self.content_stack.setCurrentWidget(self.loading_page)
        
        # For now, show login dialog immediately
        # In the future, you could check for saved tokens here
        QTimer.singleShot(100, self.show_login_dialog)  # Small delay to show loading briefly
    
    def show_login_dialog(self):
        """Show the login dialog."""
        dialog = LoginDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            credentials = dialog.get_credentials()
            # Authentication already happened in the dialog, so we can proceed directly
            self.on_auth_finished(True, credentials['username'], credentials['password'], credentials['remember'])
        else:
            # User cancelled login - exit the application completely
            QApplication.quit()  # This should terminate the application properly
    
    def login(self, username: str, password: str, remember: bool = False):
        """Perform login setup after successful authentication."""
        self.content_stack.setCurrentWidget(self.loading_page)
        self.status_bar.showMessage("Setting up your account...")
        
        self.current_user = username
        self.user_label.setText(f"Logged in as: {username}")
        
        # Setup rclone configuration
        self.rclone_manager.setup_rclone_config(username, password)
        
        # Save credentials if requested
        if remember:
            self.token_manager.save_token(username, self.api_client.token, password)
        
        # Show main window after successful login
        self.show()
        
        # Load buckets
        self.load_buckets()
    
    def on_auth_finished(self, success: bool, username: str, password: str, remember: bool):
        """Handle authentication completion."""
        if success:
            self.current_user = username
            self.user_label.setText(f"Logged in as: {username}")
            
            # Setup rclone configuration
            self.rclone_manager.setup_rclone_config(username, password)
            
            # Save credentials if requested
            if remember:
                self.token_manager.save_token(username, self.api_client.token, password)
            
            # Show main window after successful login
            self.show()
            
            # Load buckets
            self.load_buckets()
        else:
            self.show_login_error()
    
    def show_login_error(self):
        """Show login error and return to login dialog."""
        QMessageBox.critical(self, "Login Failed", 
                           "Invalid username or password. Please try again.")
        self.show_login_dialog()
    
    def load_buckets(self):
        """Load user's buckets."""
        self.status_bar.showMessage("Loading buckets...")
        
        # Create and start bucket loading worker
        self.bucket_worker = BucketWorker(self.api_client)
        self.bucket_worker.finished.connect(self.on_buckets_loaded)
        self.bucket_worker.start()
    
    def on_buckets_loaded(self, buckets: List[Dict]):
        """Handle buckets loading completion."""
        self.buckets = buckets
        self.display_buckets()
    
    def display_buckets(self):
        """Display buckets in the UI."""
        # Clear existing widgets
        for widget in self.bucket_widgets:
            widget.deleteLater()
        self.bucket_widgets.clear()
        
        # Add bucket widgets
        for bucket in self.buckets:
            widget = BucketWidget(bucket, self.current_user, self.rclone_manager)
            widget.mount_requested.connect(self.mount_bucket)
            widget.unmount_requested.connect(self.unmount_bucket)
            widget.auto_mount_changed.connect(self.toggle_auto_mount)
            
            self.bucket_widgets.append(widget)
            self.buckets_layout.insertWidget(self.buckets_layout.count() - 1, widget)
        
        if not self.buckets:
            # Show empty state
            empty_label = QLabel("No buckets found.\nCreate buckets using the web interface.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #7f8c8d; font-size: 16px; margin: 50px;")
            self.buckets_layout.insertWidget(0, empty_label)
        
        self.content_stack.setCurrentWidget(self.buckets_page)
        
        # Show helpful message about mount locations
        user_home = os.path.expanduser("~")
        bucket_count = len(self.buckets)
        if bucket_count > 0:
            self.status_bar.showMessage(f"Loaded {bucket_count} buckets • Buckets mount to {user_home}/haio-{self.current_user}-[bucket-name]")
        else:
            self.status_bar.showMessage("No buckets found")
    
    def mount_bucket(self, bucket_name: str, mount_point: str):
        """Mount a bucket."""
        self.status_bar.showMessage(f"Mounting {bucket_name}...")
        
        worker = MountWorker('mount', self.rclone_manager,
                           username=self.current_user,
                           bucket_name=bucket_name,
                           mount_point=mount_point)
        
        # Store worker to prevent premature destruction
        self.active_workers.append(worker)
        
        # Connect signals
        worker.finished.connect(lambda success, msg: self.on_mount_finished(success, msg, bucket_name, worker))
        worker.start()
    
    def unmount_bucket(self, mount_point: str):
        """Unmount a bucket."""
        self.status_bar.showMessage("Unmounting...")
        
        worker = MountWorker('unmount', self.rclone_manager, mount_point=mount_point)
        
        # Store worker to prevent premature destruction
        self.active_workers.append(worker)
        
        # Connect signals
        worker.finished.connect(lambda success, msg: self.on_unmount_finished(success, msg, worker))
        worker.start()
    
    def on_mount_finished(self, success: bool, message: str, bucket_name: str, worker: MountWorker):
        """Handle mount operation completion."""
        # Remove worker from active list
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        
        if success:
            # Show mount location in status message
            user_home = os.path.expanduser("~")
            mount_path = f"{user_home}/haio-{self.current_user}-{bucket_name}"
            self.status_bar.showMessage(f"✓ {bucket_name} mounted at {mount_path}")
        else:
            self.status_bar.showMessage(f"✗ Mount failed: {message}")
            QMessageBox.warning(self, "Mount Failed", f"Failed to mount {bucket_name}:\n{message}")
        
        # Update widget status
        for widget in self.bucket_widgets:
            widget.update_mount_status()
    
    def on_unmount_finished(self, success: bool, message: str, worker: MountWorker):
        """Handle unmount operation completion."""
        # Remove worker from active list
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        
        if success:
            self.status_bar.showMessage("✓ Unmounted successfully")
        else:
            self.status_bar.showMessage(f"✗ Unmount failed")
            
            # Show helpful dialog for unmount failures
            if "files are being accessed" in message or "busy" in message.lower():
                self.show_unmount_help_dialog(message)
            else:
                QMessageBox.warning(self, "Unmount Failed", f"Failed to unmount:\n{message}")
        
        # Update widget status
        for widget in self.bucket_widgets:
            widget.update_mount_status()
    
    def show_unmount_help_dialog(self, error_message: str):
        """Show helpful dialog for unmount issues."""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Unmount Failed - Device Busy")
        dialog.setIcon(QMessageBox.Icon.Warning)
        
        dialog.setText("Cannot unmount because files are being accessed.")
        
        detailed_text = f"""Error details: {error_message}

Common solutions:
• Close any file managers or file explorers showing this location
• Close any applications that have files open from this location  
• Close any terminal windows with current directory in this location
• Wait a moment and try again

The system will automatically retry unmounting when files are no longer in use."""
        
        dialog.setDetailedText(detailed_text)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Retry)
        dialog.setDefaultButton(QMessageBox.StandardButton.Retry)
        
        result = dialog.exec()
        if result == QMessageBox.StandardButton.Retry:
            # Find the mount point and retry unmount
            for widget in self.bucket_widgets:
                if widget.is_mounted:
                    self.unmount_bucket(widget.mount_point)
                    break
    
    def toggle_auto_mount(self, bucket_name: str, enabled: bool):
        """Toggle auto-mount at boot for a bucket."""
        if enabled:
            # Use user's home directory instead of /mnt/ to avoid permission issues
            user_home = os.path.expanduser("~")
            mount_point = f"{user_home}/haio-{self.current_user}-{bucket_name}"
            success = self.rclone_manager.create_auto_mount_service(
                self.current_user, bucket_name, mount_point, self)
            
            if success:
                self.status_bar.showMessage(f"✓ Auto-mount enabled for {bucket_name}")
            else:
                self.status_bar.showMessage(f"✗ Failed to enable auto-mount for {bucket_name}")
                platform_name = "Windows" if os.name == 'nt' else "Linux"
                QMessageBox.warning(self, "Auto-mount Failed", 
                                  f"Failed to enable auto-mount for {bucket_name}.\n"
                                  f"Make sure you have admin privileges on {platform_name}.")
        else:
            success = self.rclone_manager.remove_auto_mount_service(self.current_user, bucket_name, self)
            
            if success:
                self.status_bar.showMessage(f"✓ Auto-mount disabled for {bucket_name}")
            else:
                self.status_bar.showMessage(f"✗ Failed to disable auto-mount for {bucket_name}")
    
    def refresh_buckets(self):
        """Refresh the buckets list."""
        self.load_buckets()
    
    def logout(self):
        """Logout and return to login screen."""
        # Unmount all buckets first
        for widget in self.bucket_widgets:
            if widget.is_mounted:
                self.rclone_manager.unmount_bucket(widget.mount_point)
        
        self.current_user = None
        self.api_client.token = None
        self.user_label.setText("Not logged in")
        
        self.show_login_dialog()
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Clean up any running workers
        for worker in self.active_workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait(3000)  # Wait up to 3 seconds
        
        # Clean up auth and bucket workers if they exist
        if hasattr(self, 'auth_worker') and self.auth_worker.isRunning():
            self.auth_worker.terminate()
            self.auth_worker.wait(3000)
        
        if hasattr(self, 'bucket_worker') and self.bucket_worker.isRunning():
            self.bucket_worker.terminate()
            self.bucket_worker.wait(3000)
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Haio Smart Solutions Client")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Haio")
    
    # Create main window (but don't show it yet)
    window = HaioDriveClient()
    # Window will be shown after successful login
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
