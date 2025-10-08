# TempURL Feature Analysis & Implementation Suggestions

## Overview
The TempURL middleware in Haio smart storage allows creating temporary URLs for time-limited access to objects without requiring authentication. This is particularly useful for:
- Sharing large files without exposing credentials
- Generating download links with expiration
- Restricting access by IP address
- Creating prefix-based URLs for sharing multiple objects

## Current Documentation Summary

### Key Features
1. **Temporary Access**: Create URLs with time-limited access
2. **No Authentication Required**: Users can access objects without logging in during the validity period
3. **Prefix-Based URLs**: Share multiple objects with a common prefix
4. **IP Restrictions**: Limit access to specific IP addresses
5. **Multiple HTTP Methods**: Support for GET, POST, PUT, DELETE

### Technical Implementation

#### Method 1: Python Implementation
```python
import hmac
from hashlib import sha1
from time import time

method = 'GET'
duration_in_seconds = 60*60*24  # 24 hours
expires = int(time() + duration_in_seconds)
path = 'http://<monster_ip:port>/v1/AUTH_<projectId>/<bucket-name>/<object-name>'
key = 'secret123'
hmac_body = '%s\n%s\n%s' % (method, expires, path)
sig = hmac.new(key.encode(), hmac_body.encode(), sha1).hexdigest()
print(path + "?" + "temp_url_sig=" + sig + "&temp_url_expires=" + str(expires))
```

#### Method 2: Bash Script Implementation
```bash
# Set X-Account-Meta-Temp-URL-Key header
curl -X POST \
  -H "X-Auth-Token: $TOKEN" \
  -H "X-Account-Meta-Temp-URL-Key: $TEMPURL_KEY" \
  "$storage_url"

# Generate temporary URL
method="GET"
duration_in_seconds=$((60 * 60 * 24))  # 24 hours
path="/v1/AUTH_$user/$container/$object"
expires=$(($(date +%s) + duration_in_seconds))

# Create HMAC signature
signature=$(echo -n "${method}\n${expires}\n${path}" | openssl dgst -sha1 -hmac "$key" | cut -d' ' -f2)

# Final URL
temp_url="${path}?temp_url_sig=${signature}&temp_url_expires=${expires}"
```

### Example Output
```
http://<monster_ip:port>/v1/AUTH_<projectId>/<bucket-name>/<object-name>?temp_url_sig=f74f271e7e46dcc48256469744ef441eb3204bd6&temp_url_expires=1699165092
```

---

## Suggestions for Implementation in Haio Smart App

### 1. **Integration into Bucket Widget**

Add a "Share" button to each file/object in the bucket view:

```python
class ObjectWidget(QWidget):
    """Widget to display individual object with share functionality."""
    
    def __init__(self, object_info, bucket_name, api_client):
        super().__init__()
        self.object_info = object_info
        self.bucket_name = bucket_name
        self.api_client = api_client
        
        # Add share button
        self.share_btn = QPushButton("🔗 Share")
        self.share_btn.clicked.connect(self.show_share_dialog)
```

### 2. **TempURL Generation Dialog**

Create a user-friendly dialog for generating temporary URLs:

**Features**:
- **Duration Selection**: Dropdown or slider for 1 hour, 6 hours, 24 hours, 7 days, 30 days
- **Method Selection**: Radio buttons for GET (download), PUT (upload), POST, DELETE
- **IP Restriction** (optional): Text field for specific IP addresses
- **Generated URL Display**: Copyable text field with "Copy to Clipboard" button
- **QR Code**: Generate QR code for mobile sharing
- **Expiration Display**: Show human-readable expiration time

**UI Mock-up**:
```
┌─────────────────────────────────────────┐
│  Share File: document.pdf               │
├─────────────────────────────────────────┤
│                                         │
│  Duration: [▼ 24 hours        ]        │
│                                         │
│  Access Type: ○ Download (GET)          │
│               ○ Upload (PUT)            │
│               ○ Full Access (POST)      │
│                                         │
│  IP Restriction (Optional):             │
│  [192.168.1.100                ]        │
│                                         │
│  ┌────────────────────────────────┐    │
│  │ Generated URL:                  │    │
│  │ https://...?temp_url_sig=...   │    │
│  │ [Copy]  [QR Code]              │    │
│  └────────────────────────────────┘    │
│                                         │
│  Expires: Oct 8, 2025 at 10:00 AM      │
│                                         │
│  [Generate]  [Close]                    │
└─────────────────────────────────────────┘
```

### 3. **TempURL Manager Class**

Create a dedicated class for TempURL operations:

```python
import hmac
from hashlib import sha1
from time import time
from typing import Optional
import requests

class TempURLManager:
    """Manages temporary URL generation and validation."""
    
    def __init__(self, api_client, temp_url_key: str):
        self.api_client = api_client
        self.temp_url_key = temp_url_key
        self.base_url = api_client.base_url
    
    def set_temp_url_key(self, username: str, key: str) -> bool:
        """Set the X-Account-Meta-Temp-URL-Key header."""
        try:
            headers = {
                'X-Auth-Token': self.api_client.token,
                'X-Account-Meta-Temp-URL-Key': key
            }
            storage_url = f"{self.base_url}/v1/AUTH_{username}"
            resp = requests.post(storage_url, headers=headers)
            return resp.status_code == 204
        except Exception as e:
            print(f"Error setting temp URL key: {e}")
            return False
    
    def generate_temp_url(
        self,
        username: str,
        bucket_name: str,
        object_name: str,
        method: str = 'GET',
        duration_seconds: int = 86400,  # 24 hours default
        ip_restriction: Optional[str] = None
    ) -> str:
        """Generate a temporary URL for an object."""
        
        # Calculate expiration timestamp
        expires = int(time() + duration_seconds)
        
        # Construct the path
        path = f"/v1/AUTH_{username}/{bucket_name}/{object_name}"
        
        # Create HMAC body
        hmac_body = f"{method}\n{expires}\n{path}"
        
        # Add IP restriction if provided
        if ip_restriction:
            hmac_body += f"\nip={ip_restriction}"
        
        # Generate signature
        signature = hmac.new(
            self.temp_url_key.encode(),
            hmac_body.encode(),
            sha1
        ).hexdigest()
        
        # Construct final URL
        full_url = f"{self.base_url}{path}?temp_url_sig={signature}&temp_url_expires={expires}"
        
        if ip_restriction:
            full_url += f"&ip={ip_restriction}"
        
        return full_url
    
    def generate_prefix_url(
        self,
        username: str,
        bucket_name: str,
        prefix: str,
        method: str = 'GET',
        duration_seconds: int = 86400
    ) -> str:
        """Generate a temporary URL for all objects with a prefix."""
        
        expires = int(time() + duration_seconds)
        path = f"/v1/AUTH_{username}/{bucket_name}/{prefix}"
        
        hmac_body = f"prefix:{method}\n{expires}\n{path}"
        signature = hmac.new(
            self.temp_url_key.encode(),
            hmac_body.encode(),
            sha1
        ).hexdigest()
        
        return f"{self.base_url}{path}?temp_url_sig={signature}&temp_url_expires={expires}"
    
    def validate_temp_url(self, url: str) -> dict:
        """Validate and parse a temporary URL."""
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        sig = query_params.get('temp_url_sig', [None])[0]
        expires = query_params.get('temp_url_expires', [None])[0]
        
        if not sig or not expires:
            return {'valid': False, 'reason': 'Missing signature or expiration'}
        
        try:
            expires_int = int(expires)
            current_time = int(time())
            
            if current_time > expires_int:
                return {
                    'valid': False,
                    'reason': 'URL has expired',
                    'expired_at': expires_int
                }
            
            return {
                'valid': True,
                'expires_at': expires_int,
                'time_remaining': expires_int - current_time
            }
        except ValueError:
            return {'valid': False, 'reason': 'Invalid expiration timestamp'}
```

### 4. **Share Dialog Implementation**

```python
class ShareDialog(QDialog):
    """Dialog for generating and sharing temporary URLs."""
    
    def __init__(self, object_name, bucket_name, api_client, parent=None):
        super().__init__(parent)
        self.object_name = object_name
        self.bucket_name = bucket_name
        self.api_client = api_client
        
        self.setWindowTitle(f"Share: {object_name}")
        self.setFixedSize(500, 450)
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
            import secrets
            key = secrets.token_urlsafe(32)
            settings.setValue("temp_url_key", key)
            
            # Set it on the server
            username = self.api_client.current_user
            self.temp_url_manager.set_temp_url_key(username, key)
        
        return key
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"🔗 Share: {self.object_name}")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #3498db;")
        layout.addWidget(title)
        
        # Duration selection
        duration_label = QLabel("Valid for:")
        layout.addWidget(duration_label)
        
        self.duration_combo = QComboBox()
        self.duration_combo.addItems([
            "1 Hour",
            "6 Hours",
            "24 Hours",
            "7 Days",
            "30 Days"
        ])
        self.duration_combo.setCurrentIndex(2)  # Default: 24 hours
        layout.addWidget(self.duration_combo)
        
        # Method selection
        method_label = QLabel("Access Type:")
        layout.addWidget(method_label)
        
        self.method_group = QButtonGroup()
        self.get_radio = QRadioButton("Download (GET)")
        self.put_radio = QRadioButton("Upload (PUT)")
        self.post_radio = QRadioButton("Full Access (POST)")
        
        self.get_radio.setChecked(True)
        self.method_group.addButton(self.get_radio)
        self.method_group.addButton(self.put_radio)
        self.method_group.addButton(self.post_radio)
        
        layout.addWidget(self.get_radio)
        layout.addWidget(self.put_radio)
        layout.addWidget(self.post_radio)
        
        # IP restriction (optional)
        ip_label = QLabel("IP Restriction (Optional):")
        layout.addWidget(ip_label)
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("e.g., 192.168.1.100")
        layout.addWidget(self.ip_input)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Link")
        self.generate_btn.clicked.connect(self.generate_url)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(self.generate_btn)
        
        # Generated URL display
        self.url_display = QTextEdit()
        self.url_display.setReadOnly(True)
        self.url_display.setMaximumHeight(80)
        self.url_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 10px;
                background-color: #f8f9fa;
            }
        """)
        self.url_display.hide()
        layout.addWidget(self.url_display)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self.copy_url)
        self.copy_btn.hide()
        button_layout.addWidget(self.copy_btn)
        
        self.qr_btn = QPushButton("📱 QR Code")
        self.qr_btn.clicked.connect(self.show_qr_code)
        self.qr_btn.hide()
        button_layout.addWidget(self.qr_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Expiration info
        self.expiry_label = QLabel()
        self.expiry_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self.expiry_label.hide()
        layout.addWidget(self.expiry_label)
    
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
        else:
            method = 'POST'
        
        # Get IP restriction
        ip_restriction = self.ip_input.text().strip() or None
        
        # Generate URL
        try:
            username = self.api_client.current_user
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
            self.url_display.show()
            
            # Show action buttons
            self.copy_btn.show()
            self.qr_btn.show()
            
            # Show expiration info
            from datetime import datetime, timedelta
            expiry_time = datetime.now() + timedelta(seconds=duration)
            self.expiry_label.setText(f"Expires: {expiry_time.strftime('%B %d, %Y at %I:%M %p')}")
            self.expiry_label.show()
            
            QMessageBox.information(self, "Success", "Temporary URL generated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate URL: {str(e)}")
    
    def copy_url(self):
        """Copy URL to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.generated_url)
        QMessageBox.information(self, "Copied", "URL copied to clipboard!")
    
    def show_qr_code(self):
        """Generate and display QR code."""
        try:
            import qrcode
            from io import BytesIO
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
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
            qr_dialog.setWindowTitle("QR Code")
            layout = QVBoxLayout(qr_dialog)
            
            label = QLabel()
            label.setPixmap(pixmap)
            layout.addWidget(label)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(qr_dialog.accept)
            layout.addWidget(close_btn)
            
            qr_dialog.exec()
            
        except ImportError:
            QMessageBox.warning(self, "QR Code", 
                              "QR code generation requires 'qrcode' package.\n"
                              "Install with: pip install qrcode[pil]")
```

### 5. **Integration into Main App**

Add to `BucketWidget` or create a file browser view:

```python
# In BucketWidget or ObjectListWidget
def show_share_dialog(self, object_name):
    """Show the share dialog for an object."""
    dialog = ShareDialog(
        object_name,
        self.bucket_name,
        self.api_client,
        self
    )
    dialog.exec()
```

### 6. **Security Considerations**

**Recommendations**:
1. **Secure Key Storage**: Store `temp_url_key` securely in QSettings with encryption
2. **Key Rotation**: Implement periodic key rotation (e.g., every 90 days)
3. **Audit Log**: Log all temporary URL generation events
4. **Rate Limiting**: Implement client-side rate limiting for URL generation
5. **Validation**: Validate IP addresses and duration inputs
6. **HTTPS Only**: Ensure all URLs use HTTPS in production

### 7. **Additional Features**

**Nice-to-have additions**:
1. **URL History**: Keep a local history of generated URLs with expiration times
2. **Bulk Sharing**: Generate URLs for multiple files at once
3. **Email Integration**: Send generated URLs via email directly from the app
4. **Statistics**: Track how many times a shared URL was accessed
5. **Revocation**: Ability to revoke URLs before expiration (by changing the key)

### 8. **UI/UX Enhancements**

1. **Context Menu**: Right-click on files → "Share" option
2. **Keyboard Shortcuts**: Ctrl+Shift+S for quick sharing
3. **Drag & Drop**: Drag files to generate share links
4. **Notifications**: Desktop notifications when URLs are about to expire
5. **Dark Mode Support**: Ensure all share dialogs support dark mode

---

## Implementation Priority

### Phase 1 (Essential - Week 1)
- [ ] Implement `TempURLManager` class
- [ ] Create basic `ShareDialog` UI
- [ ] Add "Share" button to bucket widgets
- [ ] Test URL generation and validation

### Phase 2 (Important - Week 2)
- [ ] Add IP restriction support
- [ ] Implement prefix-based URLs
- [ ] Add expiration time display
- [ ] Create URL history feature

### Phase 3 (Enhancement - Week 3)
- [ ] Add QR code generation
- [ ] Implement bulk sharing
- [ ] Add email integration
- [ ] Create audit logging

### Phase 4 (Advanced - Week 4)
- [ ] Add usage statistics
- [ ] Implement key rotation
- [ ] Add desktop notifications
- [ ] Create revocation system

---

## Technical Notes

### Dependencies Required
```txt
qrcode[pil]  # For QR code generation (optional)
```

### API Endpoints Needed
```
POST /v1/AUTH_{user}
Headers:
  X-Auth-Token: {token}
  X-Account-Meta-Temp-URL-Key: {key}
```

### Environment Variables
```python
HAIO_TEMP_URL_KEY_ROTATION_DAYS = 90
HAIO_MAX_TEMP_URL_DURATION = 2592000  # 30 days
HAIO_ENABLE_IP_RESTRICTION = True
```

---

## Conclusion

The TempURL feature is a powerful addition to the Haio Smart App that will significantly improve the file sharing experience. By implementing the suggested features in phases, you can deliver a robust, secure, and user-friendly sharing system that integrates seamlessly with the existing application.

**Key Benefits**:
- ✅ Secure file sharing without credential exposure
- ✅ Time-limited access control
- ✅ IP restriction capabilities
- ✅ User-friendly interface
- ✅ QR code support for mobile devices
- ✅ Comprehensive audit trail

