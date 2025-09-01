#!/usr/bin/env python3
"""
HAIO S3 Drive Mounter - Modern Client Application
A beautiful, user-friendly client for mounting S3-compatible storage as local drives.
"""

import sys
import os
import json
import subprocess
import platform
import threading
import time
from typing import Dict, List, Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QPushButton, QLineEdit, QLabel, QMessageBox, 
    QTextEdit, QProgressBar, QGroupBox, QFrame, QCheckBox,
    QScrollArea, QStackedWidget, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem,
    QSizePolicy, QDialog, QDialogButtonBox, QFormLayout, QComboBox,
    QListWidget, QStatusBar, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QLinearGradient, QBrush
import requests


class MountThread(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, config_name, container_name, mount_point, username, password, cache_dir="/tmp/rclone-cache"):
        super().__init__()
        self.config_name = config_name
        self.container_name = container_name
        self.mount_point = mount_point
        self.username = username
        self.password = password
        self.cache_dir = cache_dir
        
    def run(self):
        try:
            # Create mount point if it doesn't exist
            os.makedirs(self.mount_point, exist_ok=True)
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Create rclone config
            self.create_rclone_config()
            
            # Mount using rclone
            cmd = [
                'rclone', 'mount',
                '--swift-no-chunk',
                '--dir-cache-time', '10s',
                '--poll-interval', '1m',
                '--vfs-cache-mode', 'full',
                '--vfs-cache-max-age', '24h',
                '--vfs-write-back', '10s',
                '--vfs-read-wait', '20ms',
                '--local-no-check-updated',
                '--no-modtime',
                '--buffer-size', '32M',
                '--attr-timeout', '1m',
                '--allow-non-empty',
                '--cache-dir', self.cache_dir,
                f'{self.config_name}:{self.container_name}',
                self.mount_point
            ]
            
            # Run rclone mount in background
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)  # Give it time to mount
            
            # Check if mount was successful
            if os.path.ismount(self.mount_point) or os.listdir(self.mount_point):
                self.finished.emit(True, "Mount successful!")
            else:
                stdout, stderr = process.communicate()
                self.finished.emit(False, f"Mount failed: {stderr.decode()}")
                
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")
    
    def create_rclone_config(self):
        config_dir = Path.home() / '.config' / 'rclone'
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / 'rclone.conf'
        
        config_content = f"""[{self.config_name}]
type = swift
user = {self.username}
key = {self.password}
auth = https://drive.haio.ir/auth/v1.0
"""
        
        # Read existing config and update or append
        existing_configs = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                content = f.read()
                # Parse existing configs
                current_section = None
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        existing_configs[current_section] = []
                    elif current_section and line:
                        existing_configs[current_section].append(line)
        
        # Update or add the new config
        existing_configs[self.config_name] = [
            'type = swift',
            f'user = {self.username}',
            f'key = {self.password}',
            'auth = https://drive.haio.ir/auth/v1.0'
        ]
        
        # Write back the config
        with open(config_file, 'w') as f:
            for section, lines in existing_configs.items():
                f.write(f'[{section}]\n')
                for line in lines:
                    f.write(f'{line}\n')
                f.write('\n')


class UnmountThread(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, mount_point):
        super().__init__()
        self.mount_point = mount_point
        
    def run(self):
        try:
            # Try to unmount using fusermount first
            result = subprocess.run(['fusermount', '-u', self.mount_point], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                # If fusermount fails, try umount
                result = subprocess.run(['umount', '-l', self.mount_point], 
                                      capture_output=True, text=True)
            
            if result.returncode == 0:
                self.finished.emit(True, "Unmount successful!")
            else:
                self.finished.emit(False, f"Unmount failed: {result.stderr}")
                
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class SystemdService:
    @staticmethod
    def create_service(service_name, config_name, container_name, mount_point, username, password, cache_dir="/tmp/rclone-cache"):
        """Create a systemd service for persistent mounting"""
        service_content = f"""[Unit]
Description=HAIO Drive Mount - {container_name}
After=network-online.target

[Service]
Environment=DrivePathDirectory="{mount_point}"
Environment=CachePathDirectory="{cache_dir}"
Environment=RcloneConfig="{Path.home()}/.config/rclone/rclone.conf"
Environment=ConfigName="{config_name}"
Environment=ContainerName="{container_name}"

Type=simple
ExecStart=/usr/bin/rclone mount \\
        --swift-no-chunk \\
        --dir-cache-time 10s \\
        --poll-interval 1m \\
        --vfs-cache-mode full \\
        --vfs-cache-max-age 24h \\
        --vfs-write-back 10s \\
        --vfs-read-wait 20ms \\
        --local-no-check-updated \\
        --no-modtime \\
        --buffer-size 32M \\
        --attr-timeout 1m \\
        --allow-non-empty \\
        --cache-dir "${{CachePathDirectory}}" \\
        --config "${{RcloneConfig}}" \\
        "${{ConfigName}}":"${{ContainerName}}" "${{DrivePathDirectory}}"
ExecStop=/bin/bash -c 'fusermount -u "${{DrivePathDirectory}}" || umount -l "${{DrivePathDirectory}}"'
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
"""
        
        service_file = f"/etc/systemd/system/{service_name}.service"
        
        try:
            # Write service file (requires sudo)
            with open(f"/tmp/{service_name}.service", 'w') as f:
                f.write(service_content)
            
            # Move to systemd directory with sudo
            subprocess.run(['sudo', 'mv', f"/tmp/{service_name}.service", service_file], check=True)
            
            # Reload systemd and enable service
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', service_name], check=True)
            
            return True, f"Service {service_name} created and enabled successfully"
        except Exception as e:
            return False, f"Failed to create service: {str(e)}"
    
    @staticmethod
    def start_service(service_name):
        try:
            subprocess.run(['sudo', 'systemctl', 'start', service_name], check=True)
            return True, f"Service {service_name} started successfully"
        except Exception as e:
            return False, f"Failed to start service: {str(e)}"
    
    @staticmethod
    def stop_service(service_name):
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=True)
            return True, f"Service {service_name} stopped successfully"
        except Exception as e:
            return False, f"Failed to stop service: {str(e)}"
    
    @staticmethod
    def remove_service(service_name):
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=False)
            subprocess.run(['sudo', 'systemctl', 'disable', service_name], check=False)
            subprocess.run(['sudo', 'rm', f"/etc/systemd/system/{service_name}.service"], check=True)
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            return True, f"Service {service_name} removed successfully"
        except Exception as e:
            return False, f"Failed to remove service: {str(e)}"


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HAIO Drive Mounter - Login")
        self.setFixedSize(400, 300)
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("HAIO Drive Mounter")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Connect to your cloud storage")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        
        layout.addSpacing(30)
        
        # Form
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter your username")
        form_layout.addRow("Username:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_edit)
        
        self.admin_url_edit = QLineEdit("http://localhost:8000")
        self.admin_url_edit.setPlaceholderText("Admin API URL")
        form_layout.addRow("Admin URL:", self.admin_url_edit)
        
        layout.addLayout(form_layout)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.attempt_login)
        self.login_button.setObjectName("primary")
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect Enter key to login
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.attempt_login)
        
    def attempt_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        admin_url = self.admin_url_edit.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return
        
        try:
            # Format username as account:username
            formatted_username = f"{username}:{username}"
            
            # Make login request to admin API
            response = requests.post(
                f"{admin_url}/login",
                json={"username": formatted_username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    # Save credentials
                    self.save_credentials(username, data.get("token"), admin_url)
                    self.accept()
                else:
                    QMessageBox.critical(self, "Login Failed", data.get("message", "Unknown error"))
            else:
                QMessageBox.critical(self, "Login Failed", f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to admin server:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{str(e)}")
    
    def save_credentials(self, username, token, admin_url):
        """Save credentials to local storage"""
        config_dir = Path.home() / '.config' / 'haio-mounter'
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / 'credentials.json'
        
        credentials = {
            "username": username,
            "token": token,
            "admin_url": admin_url,
            "saved_at": time.time()
        }
        
        with open(config_file, 'w') as f:
            json.dump(credentials, f, indent=2)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
            }
            QLabel#title {
                font-size: 24px;
                font-weight: bold;
                color: white;
                margin: 10px;
            }
            QLabel#subtitle {
                font-size: 14px;
                color: #f0f0f0;
                margin-bottom: 20px;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #ffffff30;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ffffff60;
                background: rgba(255, 255, 255, 0.2);
            }
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#primary {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
            }
            QPushButton#primary:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CBF60, stop:1 #55b059);
            }
            QPushButton:not(#primary) {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:not(#primary):hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)


class S3MountApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.username = None
        self.token = None
        self.admin_url = None
        self.mounted_drives = {}  # Track mounted drives
        
        # Try to load saved credentials
        if not self.load_credentials():
            # Show login dialog
            login_dialog = LoginDialog(self)
            if login_dialog.exec() != QDialog.DialogCode.Accepted:
                sys.exit()
            self.load_credentials()
        
        self.setWindowTitle("HAIO Drive Mounter")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.apply_styles()
        self.load_buckets()
        
    def load_credentials(self):
        """Load saved credentials"""
        try:
            config_file = Path.home() / '.config' / 'haio-mounter' / 'credentials.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    credentials = json.load(f)
                
                self.username = credentials.get("username")
                self.token = credentials.get("token")
                self.admin_url = credentials.get("admin_url")
                
                return all([self.username, self.token, self.admin_url])
        except Exception:
            pass
        return False
    
    def setup_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar, 0)
        
        # Main content area
        content_area = self.create_content_area()
        main_layout.addWidget(content_area, 1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Connected as: {self.username}")
    
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        
        layout = QVBoxLayout(sidebar)
        
        # User info
        user_info = QFrame()
        user_info.setObjectName("user_info")
        user_layout = QVBoxLayout(user_info)
        
        user_label = QLabel(f"Welcome, {self.username}")
        user_label.setObjectName("user_name")
        user_layout.addWidget(user_label)
        
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        logout_btn.setObjectName("logout_btn")
        user_layout.addWidget(logout_btn)
        
        layout.addWidget(user_info)
        
        # Navigation
        nav_frame = QFrame()
        nav_layout = QVBoxLayout(nav_frame)
        
        nav_label = QLabel("Navigation")
        nav_label.setObjectName("nav_title")
        nav_layout.addWidget(nav_label)
        
        self.buckets_btn = QPushButton("📁 My Buckets")
        self.buckets_btn.clicked.connect(lambda: self.switch_tab(0))
        self.buckets_btn.setObjectName("nav_btn")
        nav_layout.addWidget(self.buckets_btn)
        
        self.mounts_btn = QPushButton("💾 Active Mounts")
        self.mounts_btn.clicked.connect(lambda: self.switch_tab(1))
        self.mounts_btn.setObjectName("nav_btn")
        nav_layout.addWidget(self.mounts_btn)
        
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(lambda: self.switch_tab(2))
        self.settings_btn.setObjectName("nav_btn")
        nav_layout.addWidget(self.settings_btn)
        
        layout.addWidget(nav_frame)
        layout.addStretch()
        
        return sidebar
    
    def create_content_area(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabBarAutoHide(True)
        
        # Buckets tab
        self.buckets_tab = self.create_buckets_tab()
        self.tab_widget.addTab(self.buckets_tab, "Buckets")
        
        # Mounts tab
        self.mounts_tab = self.create_mounts_tab()
        self.tab_widget.addTab(self.mounts_tab, "Mounts")
        
        # Settings tab
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        return self.tab_widget
    
    def create_buckets_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QFrame()
        header.setObjectName("content_header")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("My Buckets")
        title.setObjectName("content_title")
        header_layout.addWidget(title)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_buckets)
        refresh_btn.setObjectName("refresh_btn")
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header)
        
        # Buckets list
        self.buckets_table = QTableWidget()
        self.buckets_table.setColumnCount(4)
        self.buckets_table.setHorizontalHeaderLabels(["Bucket Name", "Status", "Mount Point", "Actions"])
        
        header = self.buckets_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.buckets_table)
        
        return widget
    
    def create_mounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QFrame()
        header.setObjectName("content_header")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("Active Mounts")
        title.setObjectName("content_title")
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Mounts list
        self.mounts_table = QTableWidget()
        self.mounts_table.setColumnCount(5)
        self.mounts_table.setHorizontalHeaderLabels(["Bucket", "Mount Point", "Status", "Auto-mount", "Actions"])
        
        header = self.mounts_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.mounts_table)
        
        return widget
    
    def create_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header = QFrame()
        header.setObjectName("content_header")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("Settings")
        title.setObjectName("content_title")
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Settings form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Default mount path
        self.mount_path_edit = QLineEdit("/mnt/haio")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_mount_path)
        
        mount_layout = QHBoxLayout()
        mount_layout.addWidget(self.mount_path_edit)
        mount_layout.addWidget(browse_btn)
        
        form_layout.addRow("Default Mount Path:", mount_layout)
        
        # Cache directory
        self.cache_path_edit = QLineEdit("/tmp/rclone-cache")
        cache_browse_btn = QPushButton("Browse")
        cache_browse_btn.clicked.connect(self.browse_cache_path)
        
        cache_layout = QHBoxLayout()
        cache_layout.addWidget(self.cache_path_edit)
        cache_layout.addWidget(cache_browse_btn)
        
        form_layout.addRow("Cache Directory:", cache_layout)
        
        # Auto-start option
        self.autostart_check = QCheckBox("Start mounts at system boot")
        form_layout.addRow("", self.autostart_check)
        
        layout.addWidget(form_widget)
        layout.addStretch()
        
        return widget
    
    def switch_tab(self, index):
        self.tab_widget.setCurrentIndex(index)
        
        # Update button styles
        buttons = [self.buckets_btn, self.mounts_btn, self.settings_btn]
        for i, btn in enumerate(buttons):
            if i == index:
                btn.setObjectName("nav_btn_active")
            else:
                btn.setObjectName("nav_btn")
        
        # Re-apply styles
        self.apply_styles()
    
    def load_buckets(self):
        """Load user's buckets from the admin API"""
        try:
            response = requests.get(
                f"{self.admin_url}/user/containers",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    buckets = data.get("containers", [])
                    self.populate_buckets_table(buckets)
                else:
                    QMessageBox.warning(self, "Error", data.get("message", "Failed to load buckets"))
            else:
                QMessageBox.critical(self, "Error", f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to admin server:\n{str(e)}")
    
    def populate_buckets_table(self, buckets):
        """Populate the buckets table with data"""
        self.buckets_table.setRowCount(len(buckets))
        
        for row, bucket in enumerate(buckets):
            # Bucket name
            self.buckets_table.setItem(row, 0, QTableWidgetItem(bucket))
            
            # Status
            status = "Mounted" if bucket in self.mounted_drives else "Not Mounted"
            status_item = QTableWidgetItem(status)
            if status == "Mounted":
                status_item.setBackground(QColor("#4CAF50"))
            self.buckets_table.setItem(row, 1, status_item)
            
            # Mount point
            mount_point = self.mounted_drives.get(bucket, f"{self.mount_path_edit.text()}/{bucket}")
            self.buckets_table.setItem(row, 2, QTableWidgetItem(mount_point))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            
            if bucket in self.mounted_drives:
                unmount_btn = QPushButton("Unmount")
                unmount_btn.clicked.connect(lambda checked, b=bucket: self.unmount_bucket(b))
                unmount_btn.setObjectName("danger_btn")
                actions_layout.addWidget(unmount_btn)
            else:
                mount_btn = QPushButton("Mount")
                mount_btn.clicked.connect(lambda checked, b=bucket: self.mount_bucket(b))
                mount_btn.setObjectName("primary_btn")
                actions_layout.addWidget(mount_btn)
            
            open_btn = QPushButton("Open")
            open_btn.clicked.connect(lambda checked, b=bucket: self.open_bucket(b))
            open_btn.setObjectName("secondary_btn")
            actions_layout.addWidget(open_btn)
            
            self.buckets_table.setCellWidget(row, 3, actions_widget)
    
    def mount_bucket(self, bucket_name):
        """Mount a bucket"""
        mount_point = f"{self.mount_path_edit.text()}/{bucket_name}"
        
        # Create mount point
        os.makedirs(mount_point, exist_ok=True)
        
        # Format username for Swift auth
        swift_username = f"{self.username}:{self.username}"
        
        # Start mount thread
        self.mount_thread = MountThread(
            config_name=self.username,
            container_name=bucket_name,
            mount_point=mount_point,
            username=swift_username,
            password=self.token,  # Use token as password
            cache_dir=self.cache_path_edit.text()
        )
        
        self.mount_thread.finished.connect(lambda success, msg: self.on_mount_finished(success, msg, bucket_name, mount_point))
        self.mount_thread.start()
        
        self.status_bar.showMessage(f"Mounting {bucket_name}...")
    
    def on_mount_finished(self, success, message, bucket_name, mount_point):
        """Handle mount completion"""
        if success:
            self.mounted_drives[bucket_name] = mount_point
            self.status_bar.showMessage(f"Successfully mounted {bucket_name}")
            
            # Create systemd service if auto-start is enabled
            if self.autostart_check.isChecked():
                service_name = f"haio-{bucket_name}"
                swift_username = f"{self.username}:{self.username}"
                
                success, msg = SystemdService.create_service(
                    service_name=service_name,
                    config_name=self.username,
                    container_name=bucket_name,
                    mount_point=mount_point,
                    username=swift_username,
                    password=self.token,
                    cache_dir=self.cache_path_edit.text()
                )
                
                if success:
                    SystemdService.start_service(service_name)
        else:
            self.status_bar.showMessage(f"Failed to mount {bucket_name}: {message}")
            QMessageBox.critical(self, "Mount Error", f"Failed to mount {bucket_name}:\n{message}")
        
        self.load_buckets()  # Refresh the table
    
    def unmount_bucket(self, bucket_name):
        """Unmount a bucket"""
        if bucket_name not in self.mounted_drives:
            return
        
        mount_point = self.mounted_drives[bucket_name]
        
        # Start unmount thread
        self.unmount_thread = UnmountThread(mount_point)
        self.unmount_thread.finished.connect(lambda success, msg: self.on_unmount_finished(success, msg, bucket_name))
        self.unmount_thread.start()
        
        self.status_bar.showMessage(f"Unmounting {bucket_name}...")
    
    def on_unmount_finished(self, success, message, bucket_name):
        """Handle unmount completion"""
        if success:
            del self.mounted_drives[bucket_name]
            self.status_bar.showMessage(f"Successfully unmounted {bucket_name}")
            
            # Remove systemd service if it exists
            service_name = f"haio-{bucket_name}"
            SystemdService.remove_service(service_name)
        else:
            self.status_bar.showMessage(f"Failed to unmount {bucket_name}: {message}")
            QMessageBox.critical(self, "Unmount Error", f"Failed to unmount {bucket_name}:\n{message}")
        
        self.load_buckets()  # Refresh the table
    
    def open_bucket(self, bucket_name):
        """Open bucket in file manager"""
        mount_point = self.mounted_drives.get(bucket_name)
        if not mount_point:
            QMessageBox.warning(self, "Not Mounted", f"Bucket {bucket_name} is not mounted")
            return
        
        # Open file manager
        if platform.system() == "Linux":
            subprocess.Popen(["xdg-open", mount_point])
        elif platform.system() == "Windows":
            subprocess.Popen(["explorer", mount_point])
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", mount_point])
    
    def browse_mount_path(self):
        """Browse for mount path"""
        if platform.system() == "Windows":
            folder = QFileDialog.getExistingDirectory(
                self, "Select Mount Directory", 
                "C:\\", QFileDialog.Option.ShowDirsOnly
            )
        else:
            folder = QFileDialog.getExistingDirectory(
                self, "Select Mount Directory", 
                "/home", QFileDialog.Option.ShowDirsOnly
            )
        
        if folder:
            self.mount_path_edit.setText(folder)
    
    def browse_cache_path(self):
        """Browse for cache path"""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Cache Directory", 
            "/tmp", QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.cache_path_edit.setText(folder)
    
    def logout(self):
        """Logout and clear credentials"""
        try:
            config_file = Path.home() / '.config' / 'haio-mounter' / 'credentials.json'
            if config_file.exists():
                config_file.unlink()
        except Exception:
            pass
        
        self.close()
        
        # Restart application
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #f5f5f5;
            }
            
            QFrame#sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-right: 1px solid #ddd;
            }
            
            QFrame#user_info {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 10px;
                margin: 10px;
            }
            
            QLabel#user_name {
                color: white;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            QPushButton#logout_btn {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                padding: 5px 10px;
            }
            
            QPushButton#logout_btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            QLabel#nav_title {
                color: white;
                font-size: 14px;
                font-weight: bold;
                margin: 10px 0;
                padding: 10px;
            }
            
            QPushButton#nav_btn {
                background: transparent;
                color: white;
                border: none;
                text-align: left;
                padding: 15px 20px;
                font-size: 14px;
                border-radius: 5px;
                margin: 2px 10px;
            }
            
            QPushButton#nav_btn:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            
            QPushButton#nav_btn_active {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                text-align: left;
                padding: 15px 20px;
                font-size: 14px;
                border-radius: 5px;
                margin: 2px 10px;
                font-weight: bold;
            }
            
            QFrame#content_header {
                background: white;
                border-bottom: 1px solid #ddd;
                padding: 20px;
                margin-bottom: 10px;
            }
            
            QLabel#content_title {
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }
            
            QPushButton#refresh_btn {
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                font-weight: bold;
            }
            
            QPushButton#refresh_btn:hover {
                background: #5a6fd8;
            }
            
            QTableWidget {
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #eee;
            }
            
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            
            QTableWidget::item:selected {
                background: #667eea;
                color: white;
            }
            
            QHeaderView::section {
                background: #f8f9fa;
                border: none;
                border-bottom: 2px solid #667eea;
                padding: 10px;
                font-weight: bold;
                color: #333;
            }
            
            QPushButton#primary_btn {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            
            QPushButton#primary_btn:hover {
                background: #45a049;
            }
            
            QPushButton#secondary_btn {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            
            QPushButton#secondary_btn:hover {
                background: #1976D2;
            }
            
            QPushButton#danger_btn {
                background: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            
            QPushButton#danger_btn:hover {
                background: #d32f2f;
            }
            
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                background: white;
            }
            
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
            
            QCheckBox {
                font-size: 14px;
                color: #333;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #ddd;
                border-radius: 3px;
                background: white;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #667eea;
                border-radius: 3px;
                background: #667eea;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDZsMS0xIDEuNSAxLjVMOSAyeiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+);
            }
            
            QStatusBar {
                background: #f8f9fa;
                border-top: 1px solid #ddd;
                color: #666;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HAIO Drive Mounter")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon (you can add an icon file later)
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = S3MountApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
