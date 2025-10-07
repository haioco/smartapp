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
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QSize, QMetaObject, Q_ARG, QSettings
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QLinearGradient, QBrush, QAction, QPainterPath


class ThemeManager:
    """Manages application theme and detects system dark mode."""
    
    def __init__(self, app=None):
        self.app = app
        self.is_dark = self.detect_dark_mode()
        
        # Set up theme change monitoring
        if self.app and platform.system() == "Linux":
            # Monitor palette changes for Linux
            self.app.paletteChanged.connect(self.on_theme_changed)
    
    def on_theme_changed(self):
        """Handle system theme change."""
        old_dark = self.is_dark
        self.is_dark = self.detect_dark_mode()
        
        # If theme changed, notify all windows to refresh
        if old_dark != self.is_dark:
            if self.app:
                for widget in self.app.topLevelWidgets():
                    if hasattr(widget, 'apply_theme'):
                        widget.apply_theme()
    
    def detect_dark_mode(self) -> bool:
        """Detect if system is in dark mode."""
        system = platform.system()
        
        if system == "Windows":
            return self._detect_windows_dark_mode()
        elif system == "Darwin":  # macOS
            return self._detect_macos_dark_mode()
        else:  # Linux
            return self._detect_linux_dark_mode()
    
    def _detect_windows_dark_mode(self) -> bool:
        """Detect Windows dark mode via registry."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return value == 0  # 0 = dark mode, 1 = light mode
        except Exception:
            return False
    
    def _detect_macos_dark_mode(self) -> bool:
        """Detect macOS dark mode."""
        try:
            import subprocess
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                capture_output=True, text=True, timeout=2
            )
            return 'Dark' in result.stdout
        except Exception:
            return False
    
    def _detect_linux_dark_mode(self) -> bool:
        """Detect Linux/GTK dark mode preference."""
        try:
            # Try Qt settings first
            settings = QSettings()
            palette_variant = settings.value("QPalette")
            if palette_variant:
                app = QApplication.instance()
                if app:
                    palette = app.palette()
                    # Check if window background is darker than text
                    bg = palette.color(QPalette.ColorRole.Window)
                    fg = palette.color(QPalette.ColorRole.WindowText)
                    return bg.lightness() < fg.lightness()
            
            # Fallback: check GTK theme
            import subprocess
            result = subprocess.run(
                ['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'],
                capture_output=True, text=True, timeout=2
            )
            theme = result.stdout.strip().lower()
            return 'dark' in theme
        except Exception:
            return False
    
    def get_colors(self):
        """Get color scheme based on theme."""
        if self.is_dark:
            return {
                'bg': '#1e1e1e',
                'bg_alt': '#2d2d2d',
                'bg_widget': '#252525',
                'text': '#e0e0e0',
                'text_secondary': '#b0b0b0',
                'border': '#404040',
                'primary': '#4CAF50',
                'primary_hover': '#45a049',
                'input_bg': '#2d2d2d',
                'input_border': '#404040',
                'error_bg': '#3d2020',
                'error_border': '#5c3030',
            }
        else:
            return {
                'bg': '#ffffff',
                'bg_alt': '#f5f6fa',
                'bg_widget': '#ffffff',
                'text': '#2c3e50',
                'text_secondary': '#7f8c8d',
                'border': '#e0e0e0',
                'primary': '#4CAF50',
                'primary_hover': '#45a049',
                'input_bg': '#fafafa',
                'input_border': '#e0e0e0',
                'error_bg': '#fdf2f2',
                'error_border': '#f5c6cb',
            }


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
        # Optional: rclone log file path; when set, mount commands will include --log-file
        self.rclone_log_file: Optional[str] = None
    
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
    
    def _run_hidden_subprocess(self, cmd, **kwargs):
        """Run subprocess command without showing console window on Windows."""
        if platform.system() == "Windows":
            # Create startupinfo to hide console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
            # Add creation flags to prevent console window
            creation_flags = kwargs.get('creationflags', 0)
            creation_flags |= 0x08000000  # CREATE_NO_WINDOW
            kwargs['creationflags'] = creation_flags
            kwargs['startupinfo'] = startupinfo
        
        return subprocess.run(cmd, **kwargs)
    
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
                # Check for WinFsp.Launcher service (newer versions)
                result = subprocess.run(['sc', 'query', 'WinFsp.Launcher'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True
                
                # Fallback to check for WinFsp service (older versions)
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
    
    def test_rclone_config(self, username: str, bucket_name: str) -> tuple[bool, str]:
        """Test rclone configuration by listing the bucket."""
        try:
            config_name = f"haio_{username}"
            cmd = [
                self.rclone_executable, 'lsd',
                '--config', self.config_path,
                f'{config_name}:{bucket_name}',
                '--timeout', '10s'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return True, "Configuration test successful"
            else:
                error_msg = "Configuration test failed"
                if result.stderr.strip():
                    error_msg += f": {result.stderr.strip()}"
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            return False, "Configuration test timed out - check network connection"
        except Exception as e:
            return False, f"Configuration test error: {str(e)}"
    
    def mount_bucket(self, username: str, bucket_name: str, mount_point: str) -> tuple[bool, str]:
        """Mount a bucket using rclone."""
        try:
            # Check if mount point is a drive letter or folder path
            if platform.system() == "Windows" and mount_point.endswith(':'):
                # Mount point is a drive letter - use it directly
                print(f"Using assigned drive letter {mount_point} for mounting {bucket_name}")
            elif platform.system() == "Windows":
                # Mount point is a folder path on Windows - ensure it doesn't exist or is empty
                if os.path.exists(mount_point):
                    if os.path.isdir(mount_point) and not os.listdir(mount_point):
                        # Directory exists but is empty, remove it
                        os.rmdir(mount_point)
                    elif os.path.isdir(mount_point):
                        return False, f"Mount point {mount_point} already exists and is not empty. Please choose a different location or clear the directory."
                    else:
                        return False, f"Mount point {mount_point} already exists as a file. Please remove it first."
                
                # Create the mount point directory
                os.makedirs(mount_point, exist_ok=True)
            else:
                # Linux/Unix - create mount point normally
                os.makedirs(mount_point, exist_ok=True)
            
            # Check if already mounted
            if self.is_mounted(mount_point):
                return True, f"Bucket {bucket_name} is already mounted at {mount_point}"
            
            # Check dependencies before mounting
            if platform.system() == "Windows":
                if not self._check_winfsp_installation():
                    return False, "WinFsp is not installed. Please install WinFsp before mounting."
            
            # Test configuration first
            config_test_success, config_test_msg = self.test_rclone_config(username, bucket_name)
            if not config_test_success:
                return False, f"Configuration test failed: {config_test_msg}"
            
            # Setup rclone mount command
            config_name = f"haio_{username}"
            
            if platform.system() == "Windows":
                # Windows-specific mount command with WinFsp optimizations
                cmd = [
                    self.rclone_executable, 'mount',
                    # Note: --daemon is not supported on Windows
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
                    # Windows-specific WinFsp options
                    '--volname', f'Haio-{bucket_name}',
                    '--log-level', 'INFO',
                ]
                if self.rclone_log_file:
                    cmd += ['--log-file', self.rclone_log_file]
                cmd += [
                    f'{config_name}:{bucket_name}',
                    mount_point
                ]
            else:
                # Linux/Unix mount command
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
                ]
                if self.rclone_log_file:
                    cmd += ['--log-file', self.rclone_log_file, '--log-level', 'INFO']
                cmd += [
                    f'{config_name}:{bucket_name}',
                    mount_point
                ]
            
            print(f"Mounting {bucket_name} with command: {' '.join(cmd)}")
            
            if platform.system() == "Windows":
                # On Windows, rclone mount runs in foreground, so we start it in background
                # and check if the mount becomes available
                import threading
                import time
                
                def run_mount():
                    # Use helper function to hide console window
                    self._run_hidden_subprocess(cmd, capture_output=False, text=True)
                
                # Start mount in background thread
                mount_thread = threading.Thread(target=run_mount, daemon=True)
                mount_thread.start()
                
                # Wait for mount to become available
                for i in range(15):  # Wait up to 15 seconds
                    time.sleep(1)
                    if self.is_mounted(mount_point):
                        print(f"Mount verification successful for {bucket_name} (took {i+1} seconds)")
                        return True, f"Successfully mounted {bucket_name} at {mount_point}"
                    print(f"Waiting for mount... ({i+1}/15)")
                
                # If we get here, mount didn't become available
                error_msg = f"Mount command started but mount point did not become available for {bucket_name} after 15 seconds"
                print(error_msg)
                return False, error_msg
                
            else:
                # Linux/Unix - use daemon mode
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print(f"Mount command completed successfully for {bucket_name}")
                    # Wait a moment and check if mount is actually active
                    import time
                    time.sleep(2)
                    if self.is_mounted(mount_point):
                        print(f"Mount verification successful for {bucket_name}")
                        return True, f"Successfully mounted {bucket_name}"
                    else:
                        error_msg = f"Mount command succeeded but mount point is not active for {bucket_name}"
                        if result.stderr.strip():
                            error_msg += f"\nError details: {result.stderr.strip()}"
                        print(error_msg)
                        return False, error_msg
                else:
                    error_msg = f"Mount command failed for {bucket_name} (code: {result.returncode})"
                    if result.stderr.strip():
                        error_msg += f"\nError: {result.stderr.strip()}"
                    elif result.stdout.strip():
                        error_msg += f"\nOutput: {result.stdout.strip()}"
                    print(error_msg)
                    return False, error_msg
            
        except subprocess.TimeoutExpired:
            error_msg = f"Mount command timed out for {bucket_name}"
            print(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error mounting {bucket_name}: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def unmount_bucket(self, mount_point: str) -> tuple[bool, str]:
        """Unmount a bucket. Returns (success, message)."""
        try:
            if not os.path.exists(mount_point):
                print(f"Mount point {mount_point} does not exist")
                return True, "Mount point does not exist (already unmounted)"
            
            if not self.is_mounted(mount_point):
                print(f"Mount point {mount_point} is not mounted")
                return True, "Not currently mounted"
            
            print(f"Attempting to unmount {mount_point}")
            
            # Try different unmount commands based on platform
            if platform.system() == "Linux":
                # Try fusermount first (preferred for FUSE), then umount
                commands = [
                    ['fusermount', '-u', mount_point],
                    ['fusermount3', '-u', mount_point],
                    ['umount', mount_point]
                ]
                
                for cmd in commands:
                    try:
                        print(f"Trying command: {' '.join(cmd)}")
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            print(f"Successfully unmounted {mount_point}")
                            return True, f"Successfully unmounted {mount_point}"
                        else:
                            print(f"Command failed with code {result.returncode}: {result.stderr}")
                    except FileNotFoundError:
                        print(f"Command not found: {cmd[0]}")
                        continue
                    except subprocess.TimeoutExpired:
                        print(f"Command timed out: {' '.join(cmd)}")
                        continue
                
                # If unmount failed due to busy device, try additional strategies
                success, message = self._handle_busy_unmount(mount_point)
                return success, message
                
            else:  # Windows
                success, message = self._unmount_windows_drive(mount_point)
                return success, message
            
            return False, f"All unmount attempts failed for {mount_point}"
            
        except Exception as e:
            error_msg = f"Error unmounting {mount_point}: {e}"
            print(error_msg)
            return False, error_msg
    
    def _handle_busy_unmount(self, mount_point: str) -> tuple[bool, str]:
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
                            return True, f"Successfully unmounted {mount_point} after closing interfering processes"
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
                return True, f"Lazy unmounted {mount_point} (will complete when files are no longer in use)"
            else:
                print(f"Lazy unmount failed: {result.stderr}")
        except Exception as e:
            print(f"Lazy unmount error: {e}")
        
        print(f"All unmount strategies failed for {mount_point}")
        return False, f"Mount point {mount_point} is busy - close any applications accessing files in this location"
    
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
    
    def _unmount_windows_drive(self, mount_point: str) -> tuple[bool, str]:
        """Handle Windows-specific drive unmounting by killing rclone process."""
        try:
            drive_letter = mount_point.rstrip('\\').rstrip(':')
            if len(drive_letter) == 1:
                drive_letter += ':'
            
            print(f"Attempting to unmount Windows drive {drive_letter}")
            
            # First, try to find and kill the specific rclone process for this mount
            success = self._kill_rclone_for_mount(drive_letter)
            if success:
                # Wait a moment for the process to exit and drive to be released
                time.sleep(2)
                
                # Verify the drive is no longer mounted
                if not self.is_mounted(mount_point):
                    print(f"Successfully unmounted {drive_letter}")
                    return True, f"Successfully unmounted {drive_letter}"
                else:
                    print(f"Drive {drive_letter} still appears to be mounted after killing rclone")
            
            # If that didn't work, try a secondary targeted search using WMIC before giving up
            print(f"Trying secondary targeted unmount methods for {drive_letter}")
            try:
                import subprocess
                wmic = subprocess.run(
                    ['wmic', 'process', 'where', 'name="rclone.exe"', 'get', 'processid,commandline'],
                    capture_output=True, text=True, timeout=10
                )
                if wmic.returncode == 0:
                    pids_to_kill = []
                    for line in wmic.stdout.splitlines():
                        if 'mount' in line and (f' {drive_letter} ' in line or f' {drive_letter}\\' in line):
                            # Extract PID at end of the line if present
                            parts = line.strip().split()
                            if parts and parts[-1].isdigit():
                                pids_to_kill.append(parts[-1])
                    if pids_to_kill:
                        print(f"WMIC found targeted rclone PIDs for {drive_letter}: {pids_to_kill}")
                        for pid in pids_to_kill:
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True, text=True, timeout=5)
                            except Exception as e:
                                print(f"Failed to kill PID {pid} via WMIC fallback: {e}")
                        time.sleep(2)
                        if not self.is_mounted(mount_point):
                            print(f"Successfully unmounted {drive_letter} via WMIC-targeted kill")
                            return True, f"Successfully unmounted {drive_letter}"
                else:
                    print(f"WMIC fallback failed: {wmic.stderr}")
            except Exception as e:
                print(f"WMIC fallback error: {e}")
            
            # Last resort: try to disconnect the network drive (if it was mapped as such)
            try:
                result = subprocess.run(['net', 'use', drive_letter, '/delete', '/y'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"Successfully disconnected network drive {drive_letter}")
                    return True, f"Successfully disconnected network drive {drive_letter}"
                else:
                    print(f"Net use delete failed: {result.stderr}")
            except Exception as e:
                print(f"Net use delete error: {e}")
            
            print(f"All Windows unmount methods failed for {drive_letter}")
            
            # Return a user-friendly error message
            return False, f"Failed to unmount {drive_letter}. The mount point may be busy - close any applications accessing files in this location."
            
        except Exception as e:
            error_msg = f"Error in Windows unmount: {e}"
            print(error_msg)
            return False, error_msg
    
    def _kill_rclone_for_mount(self, drive_letter: str) -> bool:
        """Find and kill only the rclone process mounting the specified drive."""
        try:
            import subprocess
            dl = drive_letter.upper().rstrip('\\')
            if not dl.endswith(':'):
                dl = dl + ':'

            # Use PowerShell to get CommandLine for rclone processes and match the drive argument
            ps_cmd = (
                f"$d='{dl}'; "
                "Get-CimInstance Win32_Process -Filter \"name='rclone.exe'\" | "
                "Where-Object { $_.CommandLine -and ($_.CommandLine -like \"* $d*\") } | "
                "Select-Object -ExpandProperty ProcessId"
            )
            result = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_cmd],
                capture_output=True, text=True, timeout=10
            )
            pids = []
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.isdigit():
                        pids.append(line)
            else:
                print(f"PowerShell PID lookup failed: {result.stderr}")

            if not pids:
                print(f"No targeted rclone processes found for drive {dl}")
                return False

            print(f"Targeted rclone PIDs for {dl}: {pids}")
            killed_any = False
            for pid in pids:
                try:
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True, text=True, timeout=5)
                    killed_any = True
                except Exception as e:
                    print(f"Failed to kill PID {pid}: {e}")

            return killed_any

        except Exception as e:
            print(f"Error finding/killing rclone process for {drive_letter}: {e}")
            return False
    
    def is_mounted(self, mount_point: str) -> bool:
        """Check if a mount point is currently mounted."""
        try:
            if platform.system() == "Windows":
                # On Windows, check if the drive letter is accessible
                if mount_point.endswith(':'):
                    drive_letter = mount_point
                    # For drive letters like "M:", check if the drive exists and is accessible
                    try:
                        # Try to list the root directory of the drive
                        drive_path = drive_letter + "\\"
                        if os.path.exists(drive_path):
                            # Try to access the drive to verify it's mounted and accessible
                            os.listdir(drive_path)
                            return True
                        return False
                    except (OSError, PermissionError):
                        return False
                else:
                    # For folder paths, check if it exists and has content
                    return os.path.exists(mount_point) and os.path.ismount(mount_point)
            else:
                # Linux/Unix: use mountpoint command
                import subprocess
                result = subprocess.run(['mountpoint', '-q', mount_point], capture_output=True)
                return result.returncode == 0
        except Exception as e:
            print(f"Error checking mount status for {mount_point}: {e}")
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
Wants=network-online.target

[Service]
Type=notify
Environment=DrivePathDirectory="{mount_point}"
Environment=CachePathDirectory="{self.cache_dir}"
Environment=RcloneConfig="{self.config_path}"
Environment=ConfigName="{config_name}"
Environment=ContainerName="{bucket_name}"

ExecStartPre=/bin/mkdir -p "${{DrivePathDirectory}}"
ExecStartPre=/bin/mkdir -p "${{CachePathDirectory}}"
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
        --log-level INFO \\
        "${{ConfigName}}:${{ContainerName}}" "${{DrivePathDirectory}}"
ExecStop=/bin/bash -c 'fusermount -u "${{DrivePathDirectory}}" || umount -l "${{DrivePathDirectory}}"'

# Restart configuration
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=60
StartLimitBurst=3

# Resource limits
TimeoutStartSec=30
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
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

    def _is_admin(self):
        """Check if the current process is running as administrator."""
        if platform.system() != "Windows":
            return True  # Not applicable on non-Windows systems
        
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _run_as_admin(self, command, parent_widget=None):
        """Run a command with administrator privileges using UAC."""
        try:
            import ctypes
            from PyQt6.QtWidgets import QMessageBox
            
            if parent_widget:
                reply = QMessageBox.question(
                    parent_widget,
                    "Administrator Privileges Required",
                    "Creating auto-mount tasks requires administrator privileges.\n\n"
                    "Click 'Yes' to allow the application to run the command as administrator.\n"
                    "You will see a UAC (User Account Control) prompt.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return False, "User declined administrator privileges"
            
            # Use ShellExecute with 'runas' to trigger UAC prompt
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # This triggers UAC
                "powershell",
                f"-Command \"{command}\"",
                None,
                1  # SW_SHOWNORMAL
            )
            
            # ShellExecute returns a value > 32 on success
            if result > 32:
                return True, "Command executed with administrator privileges"
            else:
                return False, f"Failed to execute with administrator privileges (error code: {result})"
                
        except Exception as e:
            return False, f"Error requesting administrator privileges: {str(e)}"

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
                arg_prefix = ''  # no script path needed
            else:
                # Running as script; use the current Python interpreter and pass the script path as first arg
                exe_path = sys.executable
                arg_prefix = f'\"{os.path.abspath(__file__)}\" '
            
            # Create PowerShell command to create scheduled task
            # Use AtLogOn trigger for the current user so the mount runs in the user session, with a short delay.
            ps_command = f"""
            $exe = '{exe_path}'
            $wd = Split-Path -Parent $exe
            $args = '{arg_prefix}--auto-mount --username {username} --bucket {bucket_name} --mount-point \"{mount_point}\"'
            $Action = New-ScheduledTaskAction -Execute $exe -Argument $args -WorkingDirectory $wd
            $Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
            $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
            $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -Hidden
            Register-ScheduledTask -TaskName '{task_name}' -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
            """.strip()
            
            # Check if we're running as admin
            if not self._is_admin():
                # Request admin privileges
                success, message = self._run_as_admin(ps_command, parent_widget)
                if success:
                    # Since we can't directly get the result from the elevated process,
                    # we'll assume success and let the user know to check
                    if parent_widget:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.information(
                            parent_widget, 
                            "Auto-mount Task", 
                            f"Admin command executed for creating auto-mount task for '{bucket_name}'.\n\n"
                            f"If the UAC prompt was accepted, the task should now be created.\n"
                            f"You can verify this in Task Scheduler under 'HaioMount-{username}-{bucket_name}'."
                        )
                    return True
                else:
                    if parent_widget:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.warning(
                            parent_widget,
                            "Failed to Create Auto-mount Task",
                            f"Could not create auto-mount task: {message}\n\n"
                            f"You can manually create the task by running this application as administrator."
                        )
                    return False
            else:
                # We're already running as admin, execute directly
                result = subprocess.run(['powershell', '-Command', ps_command], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    if parent_widget:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.information(
                            parent_widget, 
                            "Auto-mount Enabled", 
                            f"Auto-mount task created successfully for '{bucket_name}'.\n"
                            f"The bucket will be mounted automatically when you log in."
                        )
                    return True
                else:
                    print(f"Failed to create Windows startup task: {result.stderr}")
                    if parent_widget:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.warning(
                            parent_widget,
                            "Failed to Create Auto-mount Task",
                            f"Could not create auto-mount task for '{bucket_name}':\n\n{result.stderr}"
                        )
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
            
            # Check if we're running as admin for removal (usually doesn't need admin but just in case)
            if not self._is_admin():
                # Try without admin first
                result = subprocess.run(['schtasks', '/Delete', '/TN', task_name, '/F'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0 and "access is denied" in result.stderr.lower():
                    # If access denied, try with admin privileges
                    command = f"schtasks /Delete /TN {task_name} /F"
                    success, message = self._run_as_admin(command, parent_widget)
                    if success:
                        if parent_widget:
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.information(
                                parent_widget, 
                                "Auto-mount Disabled", 
                                f"Auto-mount task removed for '{task_name}' (with admin privileges)."
                            )
                        return True
                    else:
                        return False
            else:
                # We're already admin or it's the first try
                result = subprocess.run(['schtasks', '/Delete', '/TN', task_name, '/F'], 
                                      capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                if parent_widget:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        parent_widget, 
                        "Auto-mount Disabled", 
                        f"Auto-mount task removed for '{task_name}'."
                    )
                return True
            else:
                # Task might not exist, which is fine - check if it's just a missing task error
                if "cannot find" in result.stderr.lower() or "does not exist" in result.stderr.lower():
                    return True
                else:
                    print(f"Failed to remove Windows startup task: {result.stderr}")
                    return False
                
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
    
    def save_token(self, username: str, token: str):
        """Save authentication token (no password)."""
        try:
            data = {}
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
            
            data[username] = {
                'token': token,
                'timestamp': time.time()
            }
            
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
            
            # Backward-compatibility migration: if plaintext password exists, encrypt it and rewrite
            entry = data.get(username)
            if entry and 'password' in entry and 'password_enc' not in entry and platform.system() == 'Windows':
                try:
                    enc = self._win_encrypt(entry['password'])
                    entry['password_enc'] = enc
                    del entry['password']
                    with open(self.token_file, 'w') as fw:
                        json.dump(data, fw, indent=2)
                except Exception as e:
                    print(f"Warning: failed to migrate plaintext password: {e}")

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

    # --- Secure password storage helpers ---
    def save_password(self, username: str, password: str) -> bool:
        """Securely store the user's password.

        On Windows, uses DPAPI (user scope) and stores the encrypted blob alongside the token.
        On other OS, stores plaintext as a minimal fallback (can be improved with keyring later).
        """
        try:
            data = {}
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
            if username not in data:
                data[username] = {'timestamp': time.time()}

            if platform.system() == 'Windows':
                enc = self._win_encrypt(password)
                data[username]['password_enc'] = enc
                # remove any legacy plaintext
                if 'password' in data[username]:
                    del data[username]['password']
            else:
                # Use base64 encoding for Linux/Mac (simple obfuscation)
                # Not as secure as Windows DPAPI but better than plaintext
                import base64
                enc_password = base64.b64encode(password.encode('utf-8')).decode('ascii')
                data[username]['password_enc'] = enc_password
                # remove any legacy plaintext
                if 'password' in data[username]:
                    del data[username]['password']

            with open(self.token_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving password: {e}")
            return False

    def get_password(self, username: str) -> Optional[str]:
        """Retrieve the stored password for the user, if available."""
        try:
            if not os.path.exists(self.token_file):
                return None
            with open(self.token_file, 'r') as f:
                data = json.load(f)
            entry = data.get(username)
            if not entry:
                return None
            if platform.system() == 'Windows':
                if 'password_enc' in entry:
                    return self._win_decrypt(entry['password_enc'])
                return entry.get('password')
            else:
                # Linux/Mac: decode base64
                if 'password_enc' in entry:
                    import base64
                    try:
                        return base64.b64decode(entry['password_enc'].encode('ascii')).decode('utf-8')
                    except Exception as e:
                        print(f"Error decoding password: {e}")
                return entry.get('password')
        except Exception as e:
            print(f"Error loading password: {e}")
            return None

    # Windows DPAPI encrypt/decrypt
    def _win_encrypt(self, plaintext: str) -> str:
        import base64, ctypes
        from ctypes import wintypes
        if plaintext is None:
            return ''
        data = plaintext.encode('utf-8')
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]
        def _to_blob(b: bytes) -> DATA_BLOB:
            buf = (ctypes.c_byte * len(b))(*b)
            return DATA_BLOB(len(b), buf)
        in_blob = _to_blob(data)
        out_blob = DATA_BLOB()
        entropy = _to_blob(b'haio-smartapp-v1')
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        if not crypt32.CryptProtectData(ctypes.byref(in_blob), None, ctypes.byref(entropy), None, None, 0, ctypes.byref(out_blob)):
            raise OSError('CryptProtectData failed')
        try:
            out_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return base64.b64encode(out_bytes).decode('ascii')
        finally:
            kernel32.LocalFree(out_blob.pbData)

    def _win_decrypt(self, b64: str) -> Optional[str]:
        import base64, ctypes
        from ctypes import wintypes
        if not b64:
            return None
        raw = base64.b64decode(b64.encode('ascii'))
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]
        def _to_blob(b: bytes) -> DATA_BLOB:
            buf = (ctypes.c_byte * len(b))(*b)
            return DATA_BLOB(len(b), buf)
        in_blob = _to_blob(raw)
        out_blob = DATA_BLOB()
        entropy = _to_blob(b'haio-smartapp-v1')
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        if not crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, ctypes.byref(entropy), None, None, 0, ctypes.byref(out_blob)):
            raise OSError('CryptUnprotectData failed')
        try:
            out_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return out_bytes.decode('utf-8', errors='ignore')
        finally:
            kernel32.LocalFree(out_blob.pbData)


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
                success, message = self.rclone_manager.mount_bucket(**self.kwargs)
            elif self.operation == 'unmount':
                mount_point = self.kwargs['mount_point']
                success, message = self.rclone_manager.unmount_bucket(mount_point)
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
        # Use user's home directory on Linux, drive letters on Windows
        if platform.system() == "Windows":
            # Try to detect if this bucket is already mounted on any drive
            detected_drive = self._find_existing_bucket_drive(bucket_info['name'], username)
            if detected_drive:
                print(f"Detected existing mount for {bucket_info['name']} at {detected_drive}:")
                self.mount_point = f"{detected_drive}:"
            else:
                print(f"No existing mount found for {bucket_info['name']}, assigning new drive letter")
                # Try to find an available drive letter for Windows using the same logic as mount_bucket
                available_drives = self._get_available_drive_letters()
                if available_drives:
                    import hashlib
                    bucket_hash = int(hashlib.md5(bucket_info['name'].encode()).hexdigest(), 16)
                    drive_index = bucket_hash % len(available_drives)
                    drive_letter = available_drives[drive_index]
                    self.mount_point = f"{drive_letter}:"
                else:
                    user_home = os.path.expanduser("~")
                    self.mount_point = os.path.join(user_home, f"haio-{username}-{bucket_info['name']}")
        else:
            # Linux/Unix - use user's home directory to avoid permission issues
            user_home = os.path.expanduser("~")
            self.mount_point = os.path.join(user_home, f"haio-{username}-{bucket_info['name']}")
        self.is_mounted = False
        
        self.setup_ui()
        self.update_mount_status()

    def _find_existing_bucket_drive(self, bucket_name: str, username: str) -> str:
        """Scan all mounted drives for a bucket that's already mounted."""
        import string
        import os

        print(f"Scanning for existing mount of bucket '{bucket_name}'...")

        # Use the volume label that rclone sets as the source of truth
        expected_volume = f"Haio-{bucket_name}"

        # Check all possible drive letters (not just existing paths)
        for letter in string.ascii_uppercase[12:]:  # Start from M
            drive_path = f"{letter}:\\"
            print(f"  Checking drive {letter}: for bucket {bucket_name}")

            try:
                # Simple drive existence check first
                if self._is_drive_accessible(letter):
                    print(f"    Drive {letter}: is accessible, checking volume label...")
                    # Only trust an exact volume label match to avoid false positives
                    if self._check_drive_volume_label(letter, expected_volume):
                        print(f"Found existing mount for {bucket_name} at {letter}: (volume label match)")
                        return letter
                else:
                    print(f"    Drive {letter}: not accessible")

            except Exception as e:
                print(f"Error checking drive {letter}: for bucket {bucket_name}: {e}")
                continue

        print(f"No existing mount found for bucket '{bucket_name}'")
        return ""
    
    def _is_drive_accessible(self, drive_letter: str) -> bool:
        """Check if a drive letter is accessible (mounted)."""
        try:
            drive_path = f"{drive_letter}:\\"
            if os.path.exists(drive_path):
                # Try to list the root directory
                os.listdir(drive_path)
                return True
        except Exception:
            pass
        return False
    
    def _is_bucket_mounted_on_drive(self, drive_letter: str, bucket_name: str) -> bool:
        """Check if a specific bucket is mounted on the given drive by analyzing rclone processes."""
        try:
            # Only check if we can find a running rclone process specifically for this bucket and drive
            import subprocess
            
            # Method 1: Use tasklist to get detailed process info
            try:
                result = subprocess.run(['wmic', 'process', 'where', 'name="rclone.exe"', 
                                       'get', 'processid,commandline'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    output = result.stdout
                    # Look for a process mounting this specific bucket to this specific drive letter
                    for line in output.split('\n'):
                        if (f':{bucket_name}' in line and 
                            f'{drive_letter}:' in line and 
                            'mount' in line):
                            print(f"    Found specific rclone process for {bucket_name} on {drive_letter}")
                            return True
                    print(f"    No specific rclone process found for {bucket_name} on {drive_letter}")
                    return False
            except Exception as e:
                print(f"    Wmic process check error: {e}")
            
            # Method 2: Fallback - check drive accessibility but don't assume it contains our bucket
            try:
                drive_path = f"{drive_letter}:\\"
                contents = os.listdir(drive_path)
                print(f"    Drive {drive_letter} accessible with {len(contents)} items, but cannot confirm bucket identity")
                # Don't assume - return False unless we can specifically identify the bucket
                return False
            except:
                print(f"    Drive {drive_letter} not accessible or empty")
                return False
            
        except Exception as e:
            print(f"    Error checking bucket {bucket_name} on drive {drive_letter}: {e}")
            return False
    
    def _check_drive_volume_label(self, drive_letter: str, expected_label: str) -> bool:
        """Check if a drive has the expected volume label."""
        # Preferred: use WinAPI for reliable, fast volume label retrieval
        try:
            label = self._get_volume_label_winapi(drive_letter)
            if label is not None:
                print(f"    WinAPI volume label for {drive_letter}: '{label}'")
                if label and expected_label.strip().lower() == label.strip().lower():
                    print(f"    Volume label match found for {drive_letter}! (WinAPI)")
                    return True
                else:
                    print(f"    No volume label match (WinAPI). Expected: '{expected_label}', Found: '{label}'")
        except Exception as e:
            print(f"    WinAPI volume check error for {drive_letter}: {e}")

        # Fallback 1: PowerShell (can be slow or unavailable on some SKUs)
        try:
            import subprocess
            result = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command',
                 f'$v = Get-Volume -ErrorAction SilentlyContinue -DriveLetter {drive_letter}; if ($v) {{ $v.FileSystemLabel }}'],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                volume_label = result.stdout.strip()
                if volume_label:
                    print(f"    PowerShell volume label for {drive_letter}: '{volume_label}'")
                    if expected_label.strip().lower() == volume_label.strip().lower():
                        print(f"    Volume label match found for {drive_letter}! (PowerShell)")
                        return True
                else:
                    print(f"    PowerShell returned empty label for {drive_letter}")
            else:
                print(f"    PowerShell volume check failed for {drive_letter}: {result.stderr.strip()}")
        except Exception as e:
            print(f"    PowerShell volume check error for {drive_letter}: {e}")
        
        # Fallback 2: legacy 'vol' command
        try:
            import subprocess
            result = subprocess.run(['vol', f'{drive_letter}:'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                output = result.stdout.strip()
                print(f"    Vol fallback for {drive_letter}: - output: {output}")
                # Try to parse the label from the line like: 'Volume in drive Q is Haio-MyBucket'
                label = None
                for line in output.splitlines():
                    if 'Volume in drive' in line and ' is ' in line:
                        try:
                            label = line.split(' is ', 1)[1].strip()
                        except Exception:
                            label = None
                        break
                if label:
                    if expected_label.strip().lower() == label.strip().lower():
                        print(f"    Volume label match found via vol for {drive_letter}!")
                        return True
                    else:
                        print(f"    Vol label did not match. Expected: '{expected_label}', Found: '{label}'")
            else:
                print(f"    Vol command failed for {drive_letter}: {result.stderr}")
        except Exception as e:
            print(f"    Vol command error for {drive_letter}: {e}")
        return False

    def _get_volume_label_winapi(self, drive_letter: str) -> str:
        """Use Windows API GetVolumeInformationW to read a drive's volume label.

        Returns the label string or an empty string if no label; returns None on API failure.
        """
        try:
            import os
            import ctypes

            root = f"{drive_letter}:\\"
            # Quick existence check; avoids unnecessary API calls on non-existent drives
            if not os.path.exists(root):
                return None

            # Prepare buffers and call
            vol_buf = ctypes.create_unicode_buffer(261)  # MAX_PATH + 1
            fs_buf = ctypes.create_unicode_buffer(261)
            serial = ctypes.c_uint32()
            max_comp = ctypes.c_uint32()
            fs_flags = ctypes.c_uint32()

            # Call the WinAPI
            res = ctypes.windll.kernel32.GetVolumeInformationW(
                ctypes.c_wchar_p(root),
                vol_buf,
                ctypes.sizeof(vol_buf),
                ctypes.byref(serial),
                ctypes.byref(max_comp),
                ctypes.byref(fs_flags),
                fs_buf,
                ctypes.sizeof(fs_buf)
            )

            if res:  # non-zero indicates success
                return vol_buf.value
            else:
                # Optionally, could retrieve GetLastError for diagnostics
                return None
        except Exception:
            return None
    
    def _is_rclone_mount(self, drive_letter: str, bucket_name: str) -> bool:
        """Check if a drive letter is an rclone mount for the specific bucket."""
        try:
            import subprocess
            # Use PowerShell to get process command lines more reliably
            result = subprocess.run(['powershell', '-Command', 
                                   'Get-WmiObject Win32_Process -Filter "name=\'rclone.exe\'" | Select-Object CommandLine'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout
                print(f"    Rclone process check for {drive_letter}: searching for ':{bucket_name}' and '{drive_letter}:'")
                # Look for a process mounting this bucket to this drive letter
                for line in output.split('\n'):
                    if (f':{bucket_name}' in line and 
                        f'{drive_letter}:' in line and 
                        'mount' in line):
                        print(f"    Found matching rclone process for {drive_letter}!")
                        return True
                print(f"    No matching rclone process found for {drive_letter}")
            else:
                print(f"    PowerShell process check failed for {drive_letter}: {result.stderr}")
        except Exception as e:
            print(f"    PowerShell process check error for {drive_letter}: {e}")
        
        # Fallback: try wmic
        try:
            result = subprocess.run(['wmic', 'process', 'where', 'name="rclone.exe"', 
                                   'get', 'commandline'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout
                print(f"    Wmic fallback for {drive_letter}: - found processes")
                # Look for a process mounting this bucket to this drive letter
                for line in output.split('\n'):
                    if (f':{bucket_name}' in line and 
                        f'{drive_letter}:' in line and 
                        'mount' in line):
                        print(f"    Wmic process match found: {line.strip()}")
                        return True
                print(f"    No wmic process match for {drive_letter} and bucket {bucket_name}")
            else:
                print(f"    Wmic command failed: {result.stderr}")
        except Exception as e:
            print(f"    Wmic command error: {e}")
        return False
    
    def _get_available_drive_letters(self):
        """Get list of available drive letters, using the same logic as mount_bucket."""
        import string
        
        # Get actually used drive letters by checking what responds
        used_drives = []
        for letter in string.ascii_uppercase:
            try:
                # Check if the drive is accessible (not just if path exists)
                test_path = f"{letter}:\\"
                if os.path.exists(test_path):
                    # Try to list the directory to see if it's actually accessible
                    try:
                        os.listdir(test_path)
                        used_drives.append(letter)
                    except (OSError, PermissionError):
                        # Drive exists but not accessible (like empty CD/DVD drives)
                        pass
            except:
                pass
        
        # Find available drive letter (skip A, B, C which are typically system drives)
        available_drives = [d for d in string.ascii_uppercase[12:] if d not in used_drives]  # Start from M
        return available_drives
    
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
        
        # AI Chat button
        self.ai_chat_btn = QPushButton("🤖 AI Chat")
        self.ai_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                margin-left: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        self.ai_chat_btn.clicked.connect(self.show_ai_feature_dialog)
        
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.auto_mount_cb)
        controls_layout.addWidget(self.ai_chat_btn)
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
    
    def show_ai_feature_dialog(self):
        """Show AI feature coming soon dialog in Persian and English."""
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QTextEdit
        
        # Create a custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("چت هوش مصنوعی - AI Chat Feature")
        dialog.setFixedSize(500, 400)
        dialog.setModal(True)
        
        # Set up the dialog layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Persian title first
        persian_title = QLabel("🤖 چت هوش مصنوعی با داده‌های شما")
        persian_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        persian_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        persian_title.setStyleSheet("color: #9b59b6; margin-bottom: 5px;")
        layout.addWidget(persian_title)
        
        # English title
        title_label = QLabel("AI Chat with Your Data")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #8e44ad; margin-bottom: 15px;")
        layout.addWidget(title_label)
        
        # Description text area
        description = QTextEdit()
        description.setReadOnly(True)
        description.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        # Bilingual content - All text center-justified
        content = """
<div style="text-align: center; margin-bottom: 20px;">
<h3 style="color: #9b59b6;">🚀 ویژگی به زودی - Coming Soon Feature</h3>
</div>

<div style="text-align: center; margin-bottom: 25px; border: 2px solid #e8f5e8; padding: 20px; border-radius: 10px;">
<h4 style="color: #2c3e50; text-align: center;">📊 تجزیه و تحلیل هوشمند داده‌ها و چت</h4>
<p style="font-size: 14px; line-height: 1.8; text-align: center;">این ویژگی انقلابی داده‌های باکت شما را به فرمت آماده هوش مصنوعی تبدیل می‌کند و امکانات زیر را فراهم می‌آورد:</p>
<ul style="padding: 0; line-height: 2; text-align: center; list-style: none;">
<li style="margin-bottom: 8px; text-align: center;">🔍 <strong>چت با اسناد شما</strong> - سوالاتی در مورد فایل‌هایتان بپرسید و پاسخ‌های فوری دریافت کنید</li>
<li style="margin-bottom: 8px; text-align: center;">📈 <strong>تجزیه و تحلیل الگوهای داده</strong> - بینش‌هایی در داده‌های ذخیره شده خود کشف کنید</li>
<li style="margin-bottom: 8px; text-align: center;">🤖 <strong>جستجوی مبتنی بر هوش مصنوعی</strong> - با استفاده از کوئری‌های زبان طبیعی اطلاعات پیدا کنید</li>
<li style="margin-bottom: 8px; text-align: center;">📋 <strong>تولید گزارش</strong> - خلاصه و تجزیه و تحلیل داده‌های خود را ایجاد کنید</li>
</ul>
</div>

<div style="text-align: center; border-top: 2px solid #e0e0e0; padding-top: 20px;">
<h4 style="color: #2c3e50; text-align: center;">📊 Smart Data Analysis & Chat</h4>
<p style="text-align: center;">This revolutionary feature will transform your bucket data into an AI-ready format, allowing you to:</p>
<ul style="line-height: 1.8; text-align: center; list-style: none; padding: 0;">
<li style="margin-bottom: 5px; text-align: center;">🔍 <strong>Chat with your documents</strong> - Ask questions about your files and get instant answers</li>
<li style="margin-bottom: 5px; text-align: center;">📈 <strong>Analyze data patterns</strong> - Discover insights in your stored data</li>
<li style="margin-bottom: 5px; text-align: center;">🤖 <strong>AI-powered search</strong> - Find information using natural language queries</li>
<li style="margin-bottom: 5px; text-align: center;">📋 <strong>Generate reports</strong> - Create summaries and analysis of your data</li>
</ul>
</div>

<div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #e8f5e8; border-radius: 8px;">
<h4 style="color: #27ae60; margin: 0; text-align: center;">🎯 منتظر این ویژگی شگفت‌انگیز باشید!</h4>
<h4 style="color: #27ae60; margin: 5px 0 0 0; text-align: center;">Stay tuned for this amazing feature!</h4>
</div>
"""
        
        description.setHtml(content)
        layout.addWidget(description)
        
        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close - بستن")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Show the dialog
        dialog.exec()


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
        
        # Initialize theme manager
        self.theme = ThemeManager()
        self.colors = self.theme.get_colors()
        
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
        c = self.colors  # Shorthand for colors
        self.setStyleSheet(f"""
            QDialog {{
                background-color: transparent;
            }}
            
            QFrame#mainFrame {{
                background-color: {c['bg']};
                border-radius: 15px;
                border: 1px solid {c['border']};
            }}
            
            QLabel#title {{
                font-size: 22px;
                font-weight: bold;
                color: {c['text']};
                margin-bottom: 5px;
                padding: 5px 0px;
            }}
            
            QLabel#subtitle {{
                font-size: 13px;
                color: {c['text_secondary']};
                padding: 2px 0px;
            }}
            
            QLabel#fieldLabel {{
                color: {c['text']};
                font-weight: bold;
                font-size: 13px;
                margin-bottom: 3px;
                padding: 3px 2px;
                background-color: transparent;
                min-height: 20px;
                max-height: 20px;
            }}
            
            QLineEdit#input {{
                border: 2px solid {c['input_border']};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                background-color: {c['input_bg']};
                color: {c['text']};
                margin: 1px 0px;
                min-height: 20px;
                max-height: 40px;
            }}
            
            QLineEdit#input:focus {{
                border-color: {c['primary']};
                background-color: {c['bg_widget']};
                outline: none;
            }}
            
            QCheckBox#checkbox {{
                color: {c['text']};
                font-size: 13px;
                margin-top: 3px;
                padding: 5px 0px;
                spacing: 8px;
                min-height: 25px;
                max-height: 25px;
            }}
            
            QCheckBox#checkbox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {c['input_border']};
                border-radius: 4px;
                background-color: {c['bg_widget']};
                margin-right: 8px;
            }}
            
            QCheckBox#checkbox::indicator:checked {{
                background-color: {c['primary']};
                border-color: {c['primary']};
                image: url(none);
            }}
            
            QLabel#errorLabel {{
                color: #e74c3c;
                background-color: {c['error_bg']};
                border: 1px solid {c['error_border']};
                border-radius: 6px;
                padding: 8px;
                margin: 5px 0px;
                font-size: 12px;
            }}
            
            QPushButton#loginButton {{
                background-color: {c['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
                min-height: 42px;
                max-height: 42px;
            }}
            
            QPushButton#loginButton:hover {{
                background-color: {c['primary_hover']};
            }}
            
            QPushButton#loginButton:pressed {{
                background-color: #3d8b40;
            }}
            
            QPushButton#cancelButton {{
                background-color: transparent;
                color: {c['text_secondary']};
                border: 2px solid {c['border']};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                min-width: 100px;
                min-height: 42px;
                max-height: 42px;
            }}
            
            QPushButton#cancelButton:hover {{
                border-color: {c['text_secondary']};
                color: {c['text']};
                background-color: {c['bg_alt']};
            }}
            
            QPushButton#cancelButton:pressed {{
                background-color: {c['bg_widget']};
            }}
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
        
        # Initialize theme manager (will be properly initialized after QApplication)
        self.theme = None
        self.colors = None
        
        # Set application icon
        self.set_application_icon()
        
        # Check dependencies on startup
        self.check_dependencies()
        
        self.current_user = None
        self.buckets = []
        self.bucket_widgets = []
        
        # Store active workers to prevent premature destruction
        self.active_workers = []
        
        # Initialize theme after QApplication is available
        self.theme = ThemeManager(QApplication.instance())
        self.colors = self.theme.get_colors()
        
        self.setup_ui()
        self.setup_styling()
        
        # Auto-login if credentials are saved
        # Don't show window initially - show only after login
        self.try_auto_login()
    
    def apply_theme(self):
        """Reapply theme when system theme changes."""
        self.colors = self.theme.get_colors()
        self.setup_styling()
        
        # Refresh all bucket widgets
        for widget in self.bucket_widgets:
            widget.update()
    
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
        """Apply application styling with theme support."""
        c = self.colors  # Shorthand for colors
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {c['bg_alt']};
            }}
            
            QFrame#header {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {c['primary']}, stop:1 {c['primary_hover']});
                border-bottom: 3px solid #3d8b40;
            }}
            
            QFrame#logoContainer {{
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 32px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }}
            
            QLabel#appTitle {{
                color: white;
                font-size: 20px;
                font-weight: bold;
            }}
            
            QLabel#userLabel {{
                color: #e8f5e8;
                font-size: 13px;
                font-weight: 500;
            }}
            
            QPushButton#headerButton {{
                background-color: rgba(255, 255, 255, 0.15);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 13px;
                margin: 0 2px;
                min-width: 90px;
            }}
            
            QPushButton#headerButton:hover {{
                background-color: rgba(255, 255, 255, 0.25);
                border-color: rgba(255, 255, 255, 0.5);
            }}
            
            QPushButton#headerButton:pressed {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            
            QLabel#loadingLabel {{
                font-size: 16px;
                color: {c['text']};
            }}
            
            QLabel#pageTitle {{
                font-size: 24px;
                font-weight: bold;
                color: {c['text']};
                margin-bottom: 20px;
            }}
            
            QScrollArea#bucketsScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QProgressBar {{
                border: 2px solid {c['border']};
                border-radius: 8px;
                text-align: center;
                background-color: {c['bg_widget']};
                color: {c['text']};
            }}
            
            QProgressBar::chunk {{
                background-color: {c['primary']};
                border-radius: 6px;
            }}
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
            self.token_manager.save_token(username, self.api_client.token)
            # Store password securely for auto-mount usage
            self.token_manager.save_password(username, password)
        
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
                self.token_manager.save_token(username, self.api_client.token)
                self.token_manager.save_password(username, password)
            
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
        self.content_stack.setCurrentWidget(self.loading_page)
        
        # Create and start bucket loading worker
        self.bucket_worker = BucketWorker(self.api_client)
        self.bucket_worker.finished.connect(self.on_buckets_loaded)
        self.bucket_worker.start()
    
    def on_buckets_loaded(self, buckets: List[Dict]):
        """Handle buckets loading completion."""
        if buckets is None:
            # API call failed, show error
            self.status_bar.showMessage("Failed to load buckets - retrying...")
            QMessageBox.warning(self, "Connection Error", 
                              "Failed to load buckets. Please check your internet connection.\n\n"
                              "Click OK to retry.")
            # Retry after 2 seconds
            QTimer.singleShot(2000, self.load_buckets)
            return
        
        self.buckets = buckets
        self.display_buckets()
    
    def display_buckets(self):
        """Display buckets in the UI."""
        # Clear existing widgets AND remove any empty state labels
        while self.buckets_layout.count() > 1:  # Keep the stretch at the end
            item = self.buckets_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.bucket_widgets.clear()
        
        # Add bucket widgets
        for bucket in self.buckets:
            widget = BucketWidget(bucket, self.current_user, self.rclone_manager)
            widget.mount_requested.connect(self.mount_bucket)
            widget.unmount_requested.connect(self.unmount_bucket)
            widget.auto_mount_changed.connect(self.toggle_auto_mount)
            
            self.bucket_widgets.append(widget)
            self.buckets_layout.insertWidget(self.buckets_layout.count() - 1, widget)
        
        # After creating all widgets, scan for existing mounts
        self.scan_existing_mounts()
        
        if not self.buckets:
            # Show empty state (only if no widgets exist)
            empty_label = QLabel("No buckets found.\nCreate buckets using the web interface.")
            empty_label.setObjectName("emptyStateLabel")
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
            # Find the bucket widget to get the actual mount point used
            mount_point = None
            for widget in self.bucket_widgets:
                if widget.bucket_info['name'] == bucket_name:
                    mount_point = widget.mount_point
                    break
            
            if mount_point:
                self.status_bar.showMessage(f"✓ {bucket_name} mounted at {mount_point}")
            else:
                self.status_bar.showMessage(f"✓ {bucket_name} mounted successfully")
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
            # Use appropriate mount point for the platform
            if platform.system() == "Windows":
                # Try to find an available drive letter for Windows
                import string
                used_drives = [d.upper() for d in string.ascii_uppercase if os.path.exists(f"{d}:")]
                available_drives = [d for d in string.ascii_uppercase if d not in used_drives and d not in ['A', 'B', 'C']]
                
                if available_drives:
                    # Use the first available drive letter
                    drive_letter = available_drives[0]
                    mount_point = f"{drive_letter}:"
                else:
                    # Fallback to folder in user's home directory
                    user_home = os.path.expanduser("~")
                    mount_point = os.path.join(user_home, f"haio-{self.current_user}-{bucket_name}")
            else:
                # Linux/Unix - use user's home directory to avoid permission issues
                user_home = os.path.expanduser("~")
                mount_point = os.path.join(user_home, f"haio-{self.current_user}-{bucket_name}")
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
    
    def scan_existing_mounts(self):
        """Scan for existing mounts and update GUI accordingly."""
        if platform.system() != "Windows":
            # This is mainly for Windows drive letter detection
            return
            
        try:
            print("Scanning for existing Windows mounts...")
            
            # Get all logical drives
            import win32api
            drives = win32api.GetLogicalDriveStrings()
            drive_list = drives.split('\000')[:-1]  # Remove empty string at end
            
            # Check each bucket widget to see if its mount point is actually mounted
            for widget in self.bucket_widgets:
                if hasattr(widget, 'mount_point') and widget.mount_point:
                    mount_point = widget.mount_point
                    
                    # For drive letters, check if they're in the system drive list
                    if mount_point.endswith(':'):
                        drive_check = mount_point + '\\'
                        if drive_check in drive_list:
                            # Double-check that it's accessible and likely an rclone mount
                            try:
                                # Try to access the drive
                                os.listdir(mount_point + "\\")
                                
                                # Check if this might be an rclone mount by looking for rclone processes
                                bucket_name = widget.bucket_info['name']
                                if self._is_likely_rclone_mount(mount_point, bucket_name):
                                    print(f"Found existing mount: {bucket_name} at {mount_point}")
                                    widget.is_mounted = True
                                    widget.update_mount_status()
                                    
                            except (OSError, PermissionError):
                                # Drive exists but not accessible, probably not our mount
                                continue
                    else:
                        # For folder mounts, use the standard check
                        if self.rclone_manager.is_mounted(mount_point):
                            print(f"Found existing folder mount: {widget.bucket_info['name']} at {mount_point}")
                            widget.is_mounted = True
                            widget.update_mount_status()
            
        except ImportError:
            print("win32api not available, using fallback mount detection")
            # Fallback: just check each widget's mount point individually
            for widget in self.bucket_widgets:
                if hasattr(widget, 'mount_point') and widget.mount_point:
                    if self.rclone_manager.is_mounted(widget.mount_point):
                        print(f"Found existing mount: {widget.bucket_info['name']} at {widget.mount_point}")
                        widget.is_mounted = True
                        widget.update_mount_status()
                        
        except Exception as e:
            print(f"Error scanning existing mounts: {e}")
    
    def _is_likely_rclone_mount(self, mount_point: str, bucket_name: str) -> bool:
        """Check if a mount point is likely an rclone mount for the given bucket."""
        try:
            # Check if there are any rclone processes running
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq rclone.exe'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'rclone.exe' in result.stdout:
                # There are rclone processes running, this could be our mount
                return True
            return False
        except Exception:
            # If we can't check processes, assume it might be our mount if it's accessible
            return True
    
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
    import argparse
    parser = argparse.ArgumentParser(description="Haio Smart Solutions Client")
    parser.add_argument('--auto-mount', action='store_true', help='Run in auto-mount mode (no UI)')
    parser.add_argument('--username', type=str, help='Username for auto-mount')
    parser.add_argument('--bucket', type=str, help='Bucket name to auto-mount')
    parser.add_argument('--mount-point', type=str, help='Mount point (drive letter like X: on Windows)')
    parser.add_argument('--log-file', type=str, help='Optional rclone log file path for auto-mount mode')
    args, unknown = parser.parse_known_args()

    if getattr(args, 'auto_mount', False):
        # Headless auto-mount flow for Scheduled Task
        try:
            username = args.username
            bucket = args.bucket
            mount_point = args.mount_point
            if not username or not bucket or not mount_point:
                print("Auto-mount requires --username, --bucket, and --mount-point")
                return 2

            # Load saved credentials (token/password) and setup rclone
            tm = TokenManager()
            saved = tm.load_token(username)
            pwd = tm.get_password(username)
            if not saved or not pwd:
                print("No saved credentials found for auto-mount; skipping")
                return 3

            api = HaioAPI()
            if not api.authenticate(username, pwd):
                print("Auto-mount auth failed")
                return 4

            mgr = RcloneManager()
            # Set default log file if provided or use a sensible default for auto-mount
            log_file = args.log_file or os.path.join(os.path.expanduser('~/.config/haio-client'), f"rclone-{bucket}.log")
            try:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                mgr.rclone_log_file = log_file
            except Exception:
                pass
            mgr.setup_rclone_config(username, pwd)

            # Ensure WinFsp on Windows
            if platform.system() == 'Windows' and not mgr._check_winfsp_installation():
                print("WinFsp missing; cannot auto-mount")
                return 5

            # Mount (idempotent if already mounted)
            ok, msg = mgr.mount_bucket(username, bucket, mount_point)
            print(msg)
            return 0 if ok else 6
        except Exception as e:
            print(f"Auto-mount error: {e}")
            return 1

    # Normal GUI mode
    app = QApplication(sys.argv)
    app.setApplicationName("Haio Smart Solutions Client")
    app.setApplicationVersion("1.5.2")
    app.setOrganizationName("Haio")
    window = HaioDriveClient()
    sys.exit(app.exec())


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
