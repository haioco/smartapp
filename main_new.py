import sys
import os
import json
import subprocess
import platform
import threading
import time
import configparser
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
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QLinearGradient, QBrush, QAction
import requests


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


class ApiError(Exception):
    pass


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
            self.rclone_executable = "rclone"
        
        self.config_path = os.path.join(self.config_dir, "rclone.conf")
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _find_rclone_executable(self):
        """Find rclone executable on Windows."""
        # Common locations for rclone on Windows
        possible_paths = [
            "rclone.exe",  # If in PATH
            os.path.join(os.path.dirname(sys.executable), "rclone.exe"),  # Same dir as python
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "rclone.exe"),  # Same dir as app
            "C:\\Program Files\\rclone\\rclone.exe",
            "C:\\Program Files (x86)\\rclone\\rclone.exe",
            os.path.join(self.home_dir, "rclone", "rclone.exe"),
        ]
        
        for path in possible_paths:
            if os.path.isfile(path) or (path == "rclone.exe" and self._check_path_executable("rclone")):
                return path
        
        return "rclone.exe"  # Fallback, assume it's in PATH
    
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
        
        # Check WinFsp on Windows  
        elif platform.system() == "Windows":
            winfsp_paths = [
                r"C:\Program Files (x86)\WinFsp\bin\launchctl-x64.exe",
                r"C:\Program Files\WinFsp\bin\launchctl-x64.exe"
            ]
            if not any(os.path.exists(path) for path in winfsp_paths):
                issues.append("WinFsp is not installed (download from: https://github.com/billziss-gh/winfsp/releases)")
        
        return issues
    
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
                return True
            
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
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error mounting {bucket_name}: {e}")
            return False
    
    def unmount_bucket(self, mount_point: str) -> bool:
        """Unmount a bucket."""
        try:
            if not self.is_mounted(mount_point):
                return True
            
            # Try fusermount first, then fallback to umount
            for cmd in [['fusermount', '-u', mount_point], ['umount', mount_point]]:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error unmounting {mount_point}: {e}")
            return False
    
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
            
            # Stop and disable service
            subprocess.run(['sudo', 'systemctl', 'stop', service_name], capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'disable', service_name], capture_output=True)
            subprocess.run(['sudo', 'rm', f"{self.service_dir}/{service_name}"], capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], capture_output=True)
            
            return True
            
        except Exception as e:
            print(f"Error removing systemd service: {e}")
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
                message = "Mounted successfully" if success else "Mount failed"
            elif self.operation == 'unmount':
                success = self.rclone_manager.unmount_bucket(self.kwargs['mount_point'])
                message = "Unmounted successfully" if success else "Unmount failed"
            else:
                success = False
                message = "Unknown operation"
            
            self.finished.emit(success, message)
            
        except Exception as e:
            self.finished.emit(False, str(e))


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
        self.setWindowTitle("Haio Drive Login")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # Remove default window decorations and add custom styling
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        self.setup_styling()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main frame
        self.main_frame = QFrame()
        self.main_frame.setObjectName("mainFrame")
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(30, 30, 30, 30)
        frame_layout.setSpacing(20)
        
        # Logo/Title
        title = QLabel("Haio Drive")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        frame_layout.addWidget(title)
        
        subtitle = QLabel("Connect to your cloud storage")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("subtitle")
        frame_layout.addWidget(subtitle)
        
        frame_layout.addSpacing(20)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setObjectName("input")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("input")
        
        self.remember_cb = QCheckBox("Remember me")
        self.remember_cb.setObjectName("checkbox")
        
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("", self.remember_cb)
        
        frame_layout.addLayout(form_layout)
        
        frame_layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.login_btn)
        
        frame_layout.addLayout(button_layout)
        
        main_layout.addWidget(self.main_frame)
        
        # Connect Enter key to login
        self.password_input.returnPressed.connect(self.accept)
    
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
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;
            }
            
            QLabel#subtitle {
                font-size: 14px;
                color: #7f8c8d;
            }
            
            QLineEdit#input {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background-color: #fafafa;
            }
            
            QLineEdit#input:focus {
                border-color: #4CAF50;
                background-color: white;
            }
            
            QCheckBox#checkbox {
                color: #34495e;
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
            }
            
            QPushButton#loginButton:hover {
                background-color: #45a049;
            }
            
            QPushButton#cancelButton {
                background-color: transparent;
                color: #7f8c8d;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                min-width: 100px;
            }
            
            QPushButton#cancelButton:hover {
                border-color: #bdc3c7;
                color: #34495e;
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
        self.try_auto_login()
    
    def check_dependencies(self):
        """Check if all required dependencies are available."""
        issues = self.rclone_manager.check_dependencies()
        
        if issues:
            issue_text = "\n".join([f"• {issue}" for issue in issues])
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Missing Dependencies")
            msg.setText("Some required dependencies are missing:")
            msg.setDetailedText(issue_text)
            
            if platform.system() == "Windows":
                msg.setInformativeText(
                    "To use this application on Windows:\n"
                    "1. Download and install WinFsp from GitHub\n"
                    "2. Download rclone.exe and place it in the same folder as this app\n"
                    "3. Restart the application"
                )
            else:
                msg.setInformativeText(
                    "To use this application on Linux:\n"
                    "1. Install rclone: curl https://rclone.org/install.sh | sudo bash\n"
                    "2. Install FUSE: sudo apt-get install fuse\n"
                    "3. Restart the application"
                )
            
            msg.exec()
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Wait for all active workers to finish
        for worker in self.active_workers:
            if worker.isRunning():
                worker.wait(3000)  # Wait up to 3 seconds
        
        event.accept()
    
    def setup_ui(self):
        self.setWindowTitle("Haio Drive Client")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
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
        title_layout = QVBoxLayout()
        
        app_title = QLabel("Haio Drive Client")
        app_title.setObjectName("appTitle")
        
        self.user_label = QLabel("Not logged in")
        self.user_label.setObjectName("userLabel")
        
        title_layout.addWidget(app_title)
        title_layout.addWidget(self.user_label)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Action buttons
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("headerButton")
        self.refresh_btn.clicked.connect(self.refresh_buckets)
        
        self.logout_btn = QPushButton("🚪 Logout")
        self.logout_btn.setObjectName("headerButton")
        self.logout_btn.clicked.connect(self.logout)
        
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.logout_btn)
        
        parent_layout.addWidget(header)
    
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
                border-bottom: 2px solid #3d8b40;
            }
            
            QLabel#appTitle {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            
            QLabel#userLabel {
                color: #e8f5e8;
                font-size: 12px;
            }
            
            QPushButton#headerButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                margin: 0 2px;
            }
            
            QPushButton#headerButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
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
        # For now, show login dialog immediately
        # In production, you might want to check for saved tokens first
        self.show_login_dialog()
    
    def show_login_dialog(self):
        """Show the login dialog."""
        dialog = LoginDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            credentials = dialog.get_credentials()
            self.login(credentials['username'], credentials['password'], credentials['remember'])
        else:
            self.close()
    
    def login(self, username: str, password: str, remember: bool = False):
        """Perform login."""
        self.content_stack.setCurrentWidget(self.loading_page)
        self.status_bar.showMessage("Authenticating...")
        
        # Perform authentication in thread
        def authenticate():
            success = self.api_client.authenticate(username, password)
            
            if success:
                self.current_user = username
                self.user_label.setText(f"Logged in as: {username}")
                
                # Setup rclone configuration
                self.rclone_manager.setup_rclone_config(username, password)
                
                # Save credentials if requested
                if remember:
                    self.token_manager.save_token(username, self.api_client.token, password)
                
                # Load buckets
                QTimer.singleShot(100, self.load_buckets)
                
            else:
                QTimer.singleShot(100, lambda: self.show_login_error())
        
        threading.Thread(target=authenticate, daemon=True).start()
    
    def show_login_error(self):
        """Show login error and return to login dialog."""
        QMessageBox.critical(self, "Login Failed", 
                           "Invalid username or password. Please try again.")
        self.show_login_dialog()
    
    def load_buckets(self):
        """Load user's buckets."""
        self.status_bar.showMessage("Loading buckets...")
        
        def fetch_buckets():
            self.buckets = self.api_client.list_containers()
            QTimer.singleShot(100, self.display_buckets)
        
        threading.Thread(target=fetch_buckets, daemon=True).start()
    
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
            self.status_bar.showMessage(f"✗ Unmount failed: {message}")
            QMessageBox.warning(self, "Unmount Failed", f"Failed to unmount:\n{message}")
        
        # Update widget status
        for widget in self.bucket_widgets:
            widget.update_mount_status()
    
    def toggle_auto_mount(self, bucket_name: str, enabled: bool):
        """Toggle auto-mount at boot for a bucket."""
        if enabled:
            # Use user's home directory instead of /mnt/ to avoid permission issues
            user_home = os.path.expanduser("~")
            mount_point = f"{user_home}/haio-{self.current_user}-{bucket_name}"
            success = self.rclone_manager.create_systemd_service(
                self.current_user, bucket_name, mount_point, self)
            
            if success:
                self.status_bar.showMessage(f"✓ Auto-mount enabled for {bucket_name}")
            else:
                self.status_bar.showMessage(f"✗ Failed to enable auto-mount for {bucket_name}")
                QMessageBox.warning(self, "Auto-mount Failed", 
                                  f"Failed to enable auto-mount for {bucket_name}.\n"
                                  "Make sure you have sudo privileges.")
        else:
            success = self.rclone_manager.remove_systemd_service(self.current_user, bucket_name, self)
            
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


def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Haio Drive Client")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Haio")
    
    # Create and show main window
    window = HaioDriveClient()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
