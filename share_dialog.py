"""
Share Dialog for Haio Smart Storage
Provides UI for generating and sharing temporary URLs
"""

import sys
import secrets
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QRadioButton, QButtonGroup, QLineEdit, QTextEdit,
    QMessageBox, QApplication, QGroupBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QPixmap
from tempurl_manager import TempURLManager


class ShareDialog(QDialog):
    """Dialog for generating and sharing temporary URLs."""
    
    def __init__(self, object_name, bucket_name, api_client, parent=None):
        super().__init__(parent)
        self.object_name = object_name
        self.bucket_name = bucket_name
        self.api_client = api_client
        self.generated_url = None
        
        self.setWindowTitle(f"Share: {object_name}")
        self.setMinimumWidth(600)
        self.setModal(True)
        
        # Initialize TempURL manager
        self.temp_url_key = self._get_or_create_temp_url_key()
        self.temp_url_manager = TempURLManager(api_client, self.temp_url_key)
        
        self.setup_ui()
    
    def _get_or_create_temp_url_key(self) -> str:
        """Get existing or create new temp URL key."""
        # Check if key exists in settings
        settings = QSettings("Haio", "SmartApp")
        key = settings.value("temp_url_key", None)
        
        if not key:
            # Generate a secure random key
            key = secrets.token_urlsafe(32)
            settings.setValue("temp_url_key", key)
            
            # Set it on the server
            username = self.api_client.username
            # Create temporary manager just to set the key
            temp_manager = TempURLManager(self.api_client, key)
            success = temp_manager.set_temp_url_key(username, key)
            if not success:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not set temp URL key on server. URL generation may fail."
                )
        
        return key
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Get theme colors
        try:
            from main_new import ThemeManager
            theme = ThemeManager()
            colors = theme.get_colors()
        except:
            colors = {
                'bg': '#ffffff',
                'text': '#2c3e50',
                'text_secondary': '#7f8c8d',
                'border': '#e0e0e0',
                'bg_widget': '#f8f9fa',
                'primary': '#3498db'
            }
        
        # Set dialog background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QGroupBox {{
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                color: {colors['text']};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            QRadioButton {{
                color: {colors['text']};
            }}
        """)
        
        # Title
        title = QLabel(f"Share File: {self.object_name}")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors['primary']};")
        layout.addWidget(title)
        
        # Duration selection group
        duration_group = QGroupBox("Valid Duration")
        duration_layout = QVBoxLayout()
        
        duration_label = QLabel("Select how long the link should be valid:")
        duration_layout.addWidget(duration_label)
        
        self.duration_combo = QComboBox()
        self.duration_combo.addItems([
            "1 Hour",
            "6 Hours",
            "24 Hours (1 Day)",
            "7 Days",
            "30 Days"
        ])
        self.duration_combo.setCurrentIndex(2)  # Default: 24 hours
        duration_layout.addWidget(self.duration_combo)
        
        duration_group.setLayout(duration_layout)
        layout.addWidget(duration_group)
        
        # Method selection group
        method_group = QGroupBox("Access Type")
        method_layout = QVBoxLayout()
        
        method_label = QLabel("Select what users can do with this link:")
        method_layout.addWidget(method_label)
        
        self.method_group = QButtonGroup()
        self.get_radio = QRadioButton("Download Only (GET) - Recommended")
        self.put_radio = QRadioButton("Upload Only (PUT)")
        self.post_radio = QRadioButton("Full Access (POST)")
        self.delete_radio = QRadioButton("Delete Access (DELETE)")
        
        self.get_radio.setChecked(True)
        self.method_group.addButton(self.get_radio)
        self.method_group.addButton(self.put_radio)
        self.method_group.addButton(self.post_radio)
        self.method_group.addButton(self.delete_radio)
        
        method_layout.addWidget(self.get_radio)
        method_layout.addWidget(self.put_radio)
        method_layout.addWidget(self.post_radio)
        method_layout.addWidget(self.delete_radio)
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # IP restriction (optional)
        ip_group = QGroupBox("IP Restriction (Optional)")
        ip_layout = QVBoxLayout()
        
        ip_label = QLabel("Restrict access to a specific IP address:")
        ip_layout.addWidget(ip_label)
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("e.g., 192.168.1.100 (leave empty for no restriction)")
        self.ip_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {colors['border']};
                border-radius: 6px;
                padding: 8px;
                background-color: {colors['bg_widget']};
                color: {colors['text']};
            }}
            QLineEdit:focus {{
                border-color: {colors['primary']};
            }}
        """)
        ip_layout.addWidget(self.ip_input)
        
        ip_group.setLayout(ip_layout)
        layout.addWidget(ip_group)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Temporary Link")
        self.generate_btn.clicked.connect(self.generate_url)
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        layout.addWidget(self.generate_btn)
        
        # Generated URL display (initially hidden)
        self.url_group = QGroupBox("Generated Temporary URL")
        url_layout = QVBoxLayout()
        
        self.url_display = QTextEdit()
        self.url_display.setReadOnly(True)
        self.url_display.setMaximumHeight(100)
        self.url_display.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {colors['primary']};
                border-radius: 6px;
                padding: 10px;
                background-color: {colors['bg_widget']};
                color: {colors['text']};
                font-family: 'Courier New', monospace;
            }}
        """)
        url_layout.addWidget(self.url_display)
        
        # Expiration info
        self.expiry_label = QLabel()
        self.expiry_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 12px; font-weight: bold;")
        url_layout.addWidget(self.expiry_label)
        
        self.url_group.setLayout(url_layout)
        self.url_group.hide()
        layout.addWidget(self.url_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_url)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.copy_btn.hide()
        button_layout.addWidget(self.copy_btn)
        
        self.qr_btn = QPushButton("Show QR Code")
        self.qr_btn.clicked.connect(self.show_qr_code)
        self.qr_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.qr_btn.hide()
        button_layout.addWidget(self.qr_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def generate_url(self):
        """Generate the temporary URL."""
        # Get duration in seconds
        duration_map = {
            0: 3600,      # 1 hour
            1: 21600,     # 6 hours
            2: 86400,     # 24 hours
            3: 604800,    # 7 days
            4: 2592000    # 30 days
        }
        duration = duration_map[self.duration_combo.currentIndex()]
        
        # Get method
        if self.get_radio.isChecked():
            method = 'GET'
        elif self.put_radio.isChecked():
            method = 'PUT'
        elif self.delete_radio.isChecked():
            method = 'DELETE'
        else:
            method = 'POST'
        
        # Get IP restriction
        ip_restriction = self.ip_input.text().strip() or None
        
        # Validate IP if provided
        if ip_restriction and not self._validate_ip(ip_restriction):
            QMessageBox.warning(
                self,
                "Invalid IP Address",
                "Please enter a valid IP address (e.g., 192.168.1.100)"
            )
            return
        
        # Generate URL
        try:
            username = self.api_client.username
            self.generated_url = self.temp_url_manager.generate_temp_url(
                username,
                self.bucket_name,
                self.object_name,
                method,
                duration,
                ip_restriction
            )
            
            # Display URL
            self.url_display.setPlainText(self.generated_url)
            self.url_group.show()
            
            # Show action buttons
            self.copy_btn.show()
            self.qr_btn.show()
            
            # Show expiration info
            expiry_time = datetime.now() + timedelta(seconds=duration)
            time_remaining = self.temp_url_manager.get_time_remaining_text(duration)
            
            self.expiry_label.setText(
                f"⏰ Expires: {expiry_time.strftime('%B %d, %Y at %I:%M %p')} "
                f"({time_remaining} from now)"
            )
            
            QMessageBox.information(
                self,
                "Success",
                "Temporary URL generated successfully!\n\n"
                "You can now copy it to clipboard or generate a QR code."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate temporary URL:\n{str(e)}"
            )
    
    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        import re
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        # Check each octet is 0-255
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    def copy_url(self):
        """Copy URL to clipboard."""
        if self.generated_url:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.generated_url)
            
            # Show success message
            QMessageBox.information(
                self,
                "Copied!",
                "Temporary URL has been copied to clipboard.\n\n"
                "You can now paste it anywhere to share the file."
            )
    
    def show_qr_code(self):
        """Generate and display QR code."""
        if not self.generated_url:
            return
        
        try:
            import qrcode
            from io import BytesIO
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.generated_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to QPixmap
            byte_array = BytesIO()
            img.save(byte_array, format='PNG')
            byte_array.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(byte_array.read())
            
            # Show in dialog
            qr_dialog = QDialog(self)
            qr_dialog.setWindowTitle("QR Code - Scan to Access File")
            qr_dialog.setModal(True)
            
            layout = QVBoxLayout(qr_dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Title
            title = QLabel("Scan this QR code with your mobile device:")
            title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            
            # QR Code image
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            
            # File info
            info_label = QLabel(f"File: {self.object_name}")
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_label.setStyleSheet("color: #7f8c8d; margin-top: 10px;")
            layout.addWidget(info_label)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(qr_dialog.accept)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border-radius: 6px;
                    padding: 10px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
            qr_dialog.exec()
            
        except ImportError:
            # QR code package not available - provide helpful alternative
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("QR Code Feature Not Available")
            msg_box.setText("QR code generation requires the 'qrcode' package.")
            msg_box.setInformativeText(
                "For now, you can copy the URL and use an online QR code generator.\n\n"
                "Recommended online QR generators:\n"
                "• qr-code-generator.com\n"
                "• qr.io\n"
                "• goqr.me"
            )
            
            # Add a button to copy URL
            copy_button = msg_box.addButton("Copy URL", QMessageBox.ButtonRole.ActionRole)
            ok_button = msg_box.addButton(QMessageBox.StandardButton.Ok)
            
            msg_box.exec()
            
            # If user clicked copy, copy the URL
            if msg_box.clickedButton() == copy_button:
                clipboard = QApplication.clipboard()
                clipboard.setText(self.generated_url)
                QMessageBox.information(self, "Copied", "URL copied to clipboard!")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate QR code:\n{str(e)}"
            )


class BulkShareDialog(QDialog):
    """Dialog for generating temporary URLs for multiple objects."""
    
    def __init__(self, object_names, bucket_name, api_client, parent=None):
        super().__init__(parent)
        self.object_names = object_names
        self.bucket_name = bucket_name
        self.api_client = api_client
        self.generated_urls = []
        
        self.setWindowTitle(f"Bulk Share - {len(object_names)} files")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.setModal(True)
        
        # Initialize TempURL manager
        self.temp_url_key = self._get_or_create_temp_url_key()
        self.temp_url_manager = TempURLManager(api_client, self.temp_url_key)
        
        self.setup_ui()
    
    def _get_or_create_temp_url_key(self) -> str:
        """Get existing or create new temp URL key."""
        settings = QSettings("Haio", "SmartApp")
        key = settings.value("temp_url_key", None)
        
        if not key:
            key = secrets.token_urlsafe(32)
            settings.setValue("temp_url_key", key)
            username = self.api_client.username
            # Create temporary manager just to set the key
            temp_manager = TempURLManager(self.api_client, key)
            temp_manager.set_temp_url_key(username, key)
        
        return key
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"Bulk Share: {len(self.object_names)} files")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #3498db;")
        layout.addWidget(title)
        
        # File list
        files_label = QLabel("Selected files:")
        layout.addWidget(files_label)
        
        files_display = QTextEdit()
        files_display.setReadOnly(True)
        files_display.setMaximumHeight(150)
        files_display.setPlainText("\n".join([f"• {name}" for name in self.object_names]))
        layout.addWidget(files_display)
        
        # Duration selection
        duration_label = QLabel("Valid for:")
        layout.addWidget(duration_label)
        
        self.duration_combo = QComboBox()
        self.duration_combo.addItems([
            "1 Hour",
            "6 Hours",
            "24 Hours (1 Day)",
            "7 Days",
            "30 Days"
        ])
        self.duration_combo.setCurrentIndex(2)
        layout.addWidget(self.duration_combo)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Links for All Files")
        self.generate_btn.clicked.connect(self.generate_urls)
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(self.generate_btn)
        
        # Results display (hidden initially)
        self.results_group = QGroupBox("Generated URLs")
        results_layout = QVBoxLayout()
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        results_layout.addWidget(self.results_display)
        
        self.results_group.setLayout(results_layout)
        self.results_group.hide()
        layout.addWidget(self.results_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.copy_all_btn = QPushButton("Copy All URLs")
        self.copy_all_btn.clicked.connect(self.copy_all_urls)
        self.copy_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.copy_all_btn.hide()
        button_layout.addWidget(self.copy_all_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def generate_urls(self):
        """Generate temporary URLs for all selected files."""
        duration_map = {
            0: 3600,      # 1 hour
            1: 21600,     # 6 hours
            2: 86400,     # 24 hours
            3: 604800,    # 7 days
            4: 2592000    # 30 days
        }
        duration = duration_map[self.duration_combo.currentIndex()]
        
        try:
            username = self.api_client.username
            self.generated_urls = []
            
            results_text = ""
            for obj_name in self.object_names:
                url = self.temp_url_manager.generate_temp_url(
                    username,
                    self.bucket_name,
                    obj_name,
                    'GET',
                    duration
                )
                self.generated_urls.append((obj_name, url))
                results_text += f"{obj_name}:\n{url}\n\n"
            
            self.results_display.setPlainText(results_text)
            self.results_group.show()
            self.copy_all_btn.show()
            
            expiry_time = datetime.now() + timedelta(seconds=duration)
            QMessageBox.information(
                self,
                "Success",
                f"Generated {len(self.generated_urls)} temporary URLs!\n\n"
                f"All links expire on: {expiry_time.strftime('%B %d, %Y at %I:%M %p')}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate URLs:\n{str(e)}"
            )
    
    def copy_all_urls(self):
        """Copy all URLs to clipboard."""
        if self.generated_urls:
            text = "\n\n".join([f"{name}:\n{url}" for name, url in self.generated_urls])
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            
            QMessageBox.information(
                self,
                "Copied!",
                f"All {len(self.generated_urls)} URLs have been copied to clipboard."
            )
