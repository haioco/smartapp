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
                f.write(f'[{section}]
')
                for line in lines:
                    f.write(f'{line}
')
                f.write('
')

class S3MountApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("S3 Drive Mounter v1.0")
        self.setGeometry(100, 100, 600, 500)
        self.setMinimumSize(500, 400)
        
        # Initialize variables
        self.mounted = False
        self.mount_thread = None
        
        # Set up the UI
        self.setup_ui()
        self.setup_styling()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to mount S3 bucket")

    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("S3 Drive Mounter")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # AWS Credentials Group
        creds_group = QGroupBox("AWS Credentials")
        creds_layout = QGridLayout(creds_group)
        
        self.aws_access_key = QLineEdit()
        self.aws_access_key.setPlaceholderText("Enter your AWS Access Key")
        self.aws_secret_key = QLineEdit()
        self.aws_secret_key.setPlaceholderText("Enter your AWS Secret Key")
        self.aws_secret_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.region_combo = QComboBox()
        self.region_combo.addItems([
            "us-east-1", "us-west-1", "us-west-2", "eu-west-1", 
            "eu-central-1", "ap-southeast-1", "ap-northeast-1"
        ])
        self.region_combo.setCurrentText("us-east-1")
        
        self.show_password_check = QCheckBox("Show password")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        
        creds_layout.addWidget(QLabel("Access Key:"), 0, 0)
        creds_layout.addWidget(self.aws_access_key, 0, 1)
        creds_layout.addWidget(QLabel("Secret Key:"), 1, 0)
        creds_layout.addWidget(self.aws_secret_key, 1, 1)
        creds_layout.addWidget(QLabel("Region:"), 2, 0)
        creds_layout.addWidget(self.region_combo, 2, 1)
        creds_layout.addWidget(self.show_password_check, 3, 1)
        
        main_layout.addWidget(creds_group)
        
        # S3 Configuration Group
        s3_group = QGroupBox("S3 Configuration")
        s3_layout = QGridLayout(s3_group)
        
        self.bucket_name = QLineEdit()
        self.bucket_name.setPlaceholderText("Enter S3 bucket name")
        
        self.mount_point = QLineEdit()
        if platform.system() == "Windows":
            self.mount_point.setPlaceholderText("e.g., Z:\\ or C:\\mount\\s3")
        else:
            self.mount_point.setPlaceholderText("e.g., /mnt/s3 or /home/user/s3")
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_mount_point)
        
        s3_layout.addWidget(QLabel("Bucket Name:"), 0, 0)
        s3_layout.addWidget(self.bucket_name, 0, 1, 1, 2)
        s3_layout.addWidget(QLabel("Mount Point:"), 1, 0)
        s3_layout.addWidget(self.mount_point, 1, 1)
        s3_layout.addWidget(self.browse_button, 1, 2)
        
        main_layout.addWidget(s3_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        
        self.mount_button = QPushButton("Mount S3 Drive")
        self.mount_button.clicked.connect(self.toggle_mount)
        self.mount_button.setDefault(True)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_all_fields)
        
        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.mount_button)
        button_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Log output
        log_group = QGroupBox("Log Output")
        log_layout = QVBoxLayout(log_group)
        
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(120)
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        main_layout.addWidget(log_group)
    def setup_styling(self):
        """Apply modern styling to the application"""
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QComboBox {
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: #f8f9fa;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 4px;
            }
        """)

    def toggle_password_visibility(self, checked):
        """Toggle password visibility"""
        if checked:
            self.aws_secret_key.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.aws_secret_key.setEchoMode(QLineEdit.EchoMode.Password)

    def browse_mount_point(self):
        """Open file dialog to select mount point"""
        if platform.system() == "Windows":
            # On Windows, let user select a directory
            folder = QFileDialog.getExistingDirectory(
                self, "Select Mount Point Directory", 
                "C:\\", QFileDialog.Option.ShowDirsOnly
            )
        else:
            # On Linux, let user select a directory
            folder = QFileDialog.getExistingDirectory(
                self, "Select Mount Point Directory", 
                "/home", QFileDialog.Option.ShowDirsOnly
            )
        
        if folder:
            self.mount_point.setText(folder)

    def clear_all_fields(self):
        """Clear all input fields"""
        self.aws_access_key.clear()
        self.aws_secret_key.clear()
        self.bucket_name.clear()
        self.mount_point.clear()
        self.log_output.clear()
        self.status_bar.showMessage("Fields cleared")

    def log_message(self, message):
        """Add message to log output"""
        self.log_output.append(f"[{threading.current_thread().name}] {message}")

    def test_connection(self):
        """Test AWS S3 connection"""
        access_key = self.aws_access_key.text()
        secret_key = self.aws_secret_key.text()
        bucket = self.bucket_name.text()
        region = self.region_combo.currentText()

        if not all([access_key, secret_key, bucket]):
            QMessageBox.warning(self, "Error", "Please fill in AWS credentials and bucket name!")
            return

        try:
            self.log_message("Testing S3 connection...")
            self.status_bar.showMessage("Testing connection...")
            
            # Test connection
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            s3 = session.client('s3')
            
            # Try to head the bucket
            s3.head_bucket(Bucket=bucket)
            
            self.log_message("✓ Connection successful!")
            self.status_bar.showMessage("Connection test successful")
            QMessageBox.information(self, "Success", "Successfully connected to S3 bucket!")
            
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            self.log_message(f"✗ {error_msg}")
            self.status_bar.showMessage("Connection test failed")
            QMessageBox.critical(self, "Connection Error", error_msg)

    def toggle_mount(self):
        if not self.mounted:
            self.mount_s3()
        else:
            self.unmount_s3()

    def mount_s3(self):
        access_key = self.aws_access_key.text().strip()
        secret_key = self.aws_secret_key.text().strip()
        bucket = self.bucket_name.text().strip()
        mount_point = self.mount_point.text().strip()
        region = self.region_combo.currentText()

        if not all([access_key, secret_key, bucket, mount_point]):
            QMessageBox.warning(self, "Error", "All fields are required!")
            return

        try:
            self.log_message(f"Mounting S3 bucket '{bucket}' to '{mount_point}'...")
            self.status_bar.showMessage("Mounting S3 bucket...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Disable UI during mount
            self.mount_button.setEnabled(False)
            self.test_button.setEnabled(False)
            
            # Create and start mount thread
            self.mount_thread = MountThread(access_key, secret_key, bucket, mount_point, region)
            self.mount_thread.success.connect(self.on_mount_success)
            self.mount_thread.error.connect(self.on_mount_error)
            self.mount_thread.start()
            
            # Update UI state
            self.mounted = True
            self.mount_button.setText("Unmount S3 Drive")
            self.mount_button.setEnabled(True)
            self.test_button.setEnabled(True)
            
            self.progress_bar.setVisible(False)
            self.log_message("✓ S3 bucket mounted successfully!")
            self.status_bar.showMessage(f"S3 bucket mounted at {mount_point}")
            
        except Exception as e:
            self.on_mount_error(str(e))

    def on_mount_success(self, message):
        """Handle successful mount"""
        self.progress_bar.setVisible(False)
        self.mount_button.setEnabled(True)
        self.test_button.setEnabled(True)
        self.log_message(f"✓ {message}")

    def on_mount_error(self, error_message):
        """Handle mount error"""
        self.progress_bar.setVisible(False)
        self.mount_button.setEnabled(True)
        self.test_button.setEnabled(True)
        self.mounted = False
        self.mount_button.setText("Mount S3 Drive")
        
        error_msg = f"Failed to mount: {error_message}"
        self.log_message(f"✗ {error_msg}")
        self.status_bar.showMessage("Mount failed")
        QMessageBox.critical(self, "Mount Error", error_msg)

    def unmount_s3(self):
        mount_point = self.mount_point.text().strip()
        try:
            self.log_message(f"Unmounting S3 drive from '{mount_point}'...")
            self.status_bar.showMessage("Unmounting S3 drive...")
            
            # Terminate mount thread if running
            if self.mount_thread and self.mount_thread.isRunning():
                self.mount_thread.terminate()
                self.mount_thread.wait()
            
            # Platform-specific unmount
            if platform.system() == "Windows":
                os.system(f'net use {mount_point} /delete')
            else:
                os.system(f'fusermount -u "{mount_point}" 2>/dev/null || umount "{mount_point}" 2>/dev/null')
            
            self.mounted = False
            self.mount_button.setText("Mount S3 Drive")
            self.log_message("✓ S3 drive unmounted successfully!")
            self.status_bar.showMessage("S3 drive unmounted")
            
        except Exception as e:
            error_msg = f"Failed to unmount: {str(e)}"
            self.log_message(f"✗ {error_msg}")
            self.status_bar.showMessage("Unmount failed")
            QMessageBox.critical(self, "Unmount Error", error_msg)

    def closeEvent(self, event):
        """Handle application close"""
        if self.mounted:
            reply = QMessageBox.question(
                self, 'Exit Application', 
                'S3 drive is still mounted. Do you want to unmount and exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.unmount_s3()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

        
        self.mounted = False
        self.fuse_process = None

    def toggle_mount(self):
        if not self.mounted:
            self.mount_s3()
        else:
            self.unmount_s3()

    def mount_s3(self):
        access_key = self.aws_access_key.text()
        secret_key = self.aws_secret_key.text()
        bucket = self.bucket_name.text()
        mount_point = self.mount_point.text()

        if not all([access_key, secret_key, bucket, mount_point]):
            QMessageBox.warning(self, "Error", "All fields are required!")
            return

        try:
            # Create mount point if it doesn't exist
            os.makedirs(mount_point, exist_ok=True)

            # Initialize S3FileSystem
            s3 = S3FileSystem(key=access_key, secret=secret_key)
            
            def mount():
                FUSE(s3, mount_point, nothreads=True, foreground=True)

            # Start FUSE mount in a separate thread
            self.fuse_process = threading.Thread(target=mount)
            self.fuse_process.start()
            
            self.mounted = True
            self.mount_button.setText("Unmount")
            QMessageBox.information(self, "Success", f"S3 bucket mounted at {mount_point}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to mount: {str(e)}")

    def unmount_s3(self):
        mount_point = self.mount_point.text()
        try:
            if sys.platform == "win32":
                os.system(f"fusermount -u {mount_point}")
            else:
                os.system(f"umount {mount_point}")
            
            self.mounted = False
            self.mount_button.setText("Mount")
            QMessageBox.information(self, "Success", "S3 bucket unmounted successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to unmount: {str(e)}")

    def closeEvent(self, event):
        if self.mounted:
            self.unmount_s3()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = S3MountApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
