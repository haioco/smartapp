# TempURL Feature Implementation Guide

## Overview

The TempURL (Temporary URL) feature has been successfully integrated into the Haio Smart Storage application. This feature allows users to generate time-limited, secure URLs for sharing files without exposing credentials.

## Implementation Date
October 7, 2025

## Files Added/Modified

### New Files Created:

1. **`tempurl_manager.py`** - Core TempURL management class
   - Handles URL generation and validation
   - Implements HMAC-SHA1 signature generation
   - Supports IP restrictions and prefix-based URLs

2. **`share_dialog.py`** - User interface components
   - `ShareDialog`: Single file sharing with advanced options
   - `BulkShareDialog`: Multiple file sharing
   - QR code generation support

3. **`bucket_browser.py`** - File browser with sharing capabilities
   - `BucketBrowserDialog`: Browse and share bucket contents
   - Search and filter functionality
   - Context menu support

### Modified Files:

1. **`main_new.py`**
   - Added imports for TempURL components
   - Integrated "Browse & Share" button in `BucketWidget`
   - Added `show_bucket_browser()` method

2. **`requirements.txt`**
   - Added `qrcode[pil]>=7.4.2` for QR code generation

## Features Implemented

### 1. Core TempURL Management (`tempurl_manager.py`)

**Key Methods:**
- `set_temp_url_key(username, key)`: Sets the secret key for URL signing
- `generate_temp_url()`: Creates temporary URLs for single objects
- `generate_prefix_url()`: Creates URLs for multiple objects with common prefix
- `validate_temp_url()`: Validates and checks expiration of URLs
- `get_human_readable_expiry()`: Converts timestamps to readable format

**Security Features:**
- HMAC-SHA1 signature generation
- Time-based expiration
- IP address restriction support
- Secure key storage using QSettings

### 2. Share Dialog (`share_dialog.py`)

**Single File Sharing (`ShareDialog`):**
- Duration selection (1 hour to 30 days)
- Access type selection:
  - 📥 Download Only (GET) - Recommended
  - 📤 Upload Only (PUT)
  - 🔓 Full Access (POST)
  - 🗑️ Delete Access (DELETE)
- Optional IP restriction
- QR code generation
- Copy to clipboard functionality

**Bulk File Sharing (`BulkShareDialog`):**
- Share multiple files at once
- Batch URL generation
- Copy all URLs at once
- Expiration time display

### 3. Bucket Browser (`bucket_browser.py`)

**Features:**
- File listing with search/filter
- Sortable table view
- Context menu (right-click) support
- Multi-file selection
- Quick share buttons
- Background loading with progress indicator

**Columns Displayed:**
- File name
- Size (human-readable)
- Last modified date
- Action buttons

### 4. UI Integration

**New Button Added to Each Bucket:**
```
📂 Browse & Share
```

**Button Features:**
- Opens bucket browser dialog
- Shows all files in the bucket
- Allows sharing via temporary URLs
- Integrated with existing UI theme

## Usage Instructions

### For End Users:

#### Sharing a Single File:

1. Click **"📂 Browse & Share"** on any bucket
2. Find the file you want to share
3. Click the **"🔗 Share"** button next to the file
4. Configure sharing options:
   - **Duration**: How long the link will be valid
   - **Access Type**: What the recipient can do
   - **IP Restriction**: (Optional) Limit to specific IP
5. Click **"🔗 Generate Temporary Link"**
6. Options:
   - **📋 Copy to Clipboard**: Copy the URL
   - **📱 Show QR Code**: Display scannable QR code

#### Sharing Multiple Files:

1. Click **"📂 Browse & Share"** on any bucket
2. Select multiple files (Ctrl+Click or Shift+Click)
3. Click **"🔗 Share Selected (X)"** button
4. Configure duration
5. All URLs will be generated at once

#### Using Context Menu:

1. Right-click on any file in the browser
2. Options:
   - **🔗 Share this file**: Share single file
   - **📋 Copy filename**: Copy name to clipboard
   - **🔗 Share all selected**: Share multiple files

### For Developers:

#### Integrating TempURL in Other Components:

```python
from tempurl_manager import TempURLManager
from share_dialog import ShareDialog

# In your code:
def share_file(self, object_name, bucket_name):
    """Share a file with temporary URL."""
    dialog = ShareDialog(
        object_name,
        bucket_name,
        self.api_client,
        self
    )
    dialog.exec()
```

#### Generating URLs Programmatically:

```python
from tempurl_manager import TempURLManager
import secrets

# Initialize
temp_url_key = secrets.token_urlsafe(32)
manager = TempURLManager(api_client, temp_url_key)

# Set key on server
manager.set_temp_url_key(username, temp_url_key)

# Generate URL
url = manager.generate_temp_url(
    username="testuser",
    bucket_name="mybucket",
    object_name="document.pdf",
    method='GET',
    duration_seconds=86400,  # 24 hours
    ip_restriction="192.168.1.100"  # Optional
)

print(url)
```

#### URL Format:

```
https://drive.haio.ir/v1/AUTH_username/bucket/object?temp_url_sig=SIGNATURE&temp_url_expires=TIMESTAMP&ip=IP_ADDRESS
```

## Technical Details

### Security Implementation

1. **Key Generation:**
   - Uses `secrets.token_urlsafe(32)` for cryptographically secure keys
   - Stored in QSettings with application scope
   - Key is set once and reused for all URLs

2. **Signature Generation:**
   ```python
   hmac_body = f"{method}\n{expires}\n{path}"
   signature = hmac.new(key.encode(), hmac_body.encode(), sha1).hexdigest()
   ```

3. **Expiration:**
   - Unix timestamp-based
   - Server-side validation
   - Client-side display of remaining time

### API Endpoints Used

```http
POST /v1/AUTH_{username}
Headers:
  X-Auth-Token: {token}
  X-Account-Meta-Temp-URL-Key: {secret_key}
```

### Configuration Storage

**QSettings Keys:**
- `Haio/SmartApp/temp_url_key`: Encrypted storage of URL signing key

### Error Handling

- **No API Client**: Warning dialog shown
- **Not Authenticated**: Login prompt
- **Network Errors**: Clear error messages
- **Invalid IP**: Format validation with user feedback
- **QR Code Unavailable**: Fallback message with install instructions

## Dependencies

### Required Python Packages:
```
PyQt6>=6.7.1          # GUI framework
requests>=2.28.0      # HTTP requests
qrcode[pil]>=7.4.2    # QR code generation
```

### System Requirements:
- Python 3.8+
- Internet connection (for API calls)
- Display with GUI support

## Testing Checklist

- [x] Single file sharing
- [x] Multiple file sharing
- [x] Duration selection
- [x] Access type selection
- [x] IP restriction
- [x] QR code generation
- [x] URL validation
- [x] Copy to clipboard
- [x] Search/filter in browser
- [x] Context menu
- [x] Theme compatibility (light/dark mode)
- [x] Error handling
- [x] Background loading

## Known Limitations

1. **QR Code Generation**: Requires `qrcode[pil]` package installation
   - If not available, user is shown install instructions
   
2. **IP Restriction**: Only supports single IP address
   - Multiple IPs require server-side support
   
3. **URL Validation**: Client-side only
   - Server must validate signatures and expiration

4. **Key Rotation**: Not implemented
   - Consider implementing periodic key rotation for enhanced security

## Future Enhancements

### Phase 2 (Planned):
- [ ] URL history tracking
- [ ] Email integration
- [ ] Usage statistics
- [ ] Bulk operations optimization
- [ ] Advanced filtering

### Phase 3 (Planned):
- [ ] Key rotation mechanism
- [ ] Revocation system
- [ ] Audit logging
- [ ] Desktop notifications
- [ ] Prefix-based URL UI

### Phase 4 (Advanced):
- [ ] Analytics dashboard
- [ ] Integration with external sharing platforms
- [ ] Custom expiration times
- [ ] Password-protected URLs

## Troubleshooting

### Issue: "TempURL feature not available"
**Solution**: Ensure all modules are installed:
```bash
pip install -r requirements.txt
```

### Issue: "Could not set temp URL key on server"
**Solution**: 
- Check authentication token
- Verify network connection
- Ensure server supports TempURL middleware

### Issue: "QR Code generation requires 'qrcode' package"
**Solution**: Install the package:
```bash
pip install qrcode[pil]
```

### Issue: Generated URL doesn't work
**Solution**:
- Verify URL hasn't expired
- Check if IP restriction matches client IP
- Ensure TempURL key is set on server

## Performance Considerations

1. **Object List Loading**: 
   - Loads in background thread
   - Shows progress indicator
   - No UI blocking

2. **Bulk URL Generation**:
   - Sequential generation
   - Progress feedback
   - Memory efficient

3. **Search/Filter**:
   - Client-side filtering
   - Instant results
   - No API calls

## Security Best Practices

1. **Key Management**:
   - Generate new keys periodically
   - Use secure storage (QSettings)
   - Never log or display keys

2. **URL Sharing**:
   - Use shortest necessary duration
   - Consider IP restrictions for sensitive files
   - Use GET (download) for read-only access

3. **Access Control**:
   - Different access types for different use cases
   - Monitor URL usage if possible
   - Revoke compromised keys immediately

## API Reference

### TempURLManager Class

```python
class TempURLManager:
    """Manages temporary URL generation and validation."""
    
    def __init__(self, api_client, temp_url_key: str)
    def set_temp_url_key(self, username: str, key: str) -> bool
    def generate_temp_url(
        self,
        username: str,
        bucket_name: str,
        object_name: str,
        method: str = 'GET',
        duration_seconds: int = 86400,
        ip_restriction: Optional[str] = None
    ) -> str
    def generate_prefix_url(
        self,
        username: str,
        bucket_name: str,
        prefix: str,
        method: str = 'GET',
        duration_seconds: int = 86400
    ) -> str
    def validate_temp_url(self, url: str) -> Dict
```

### ShareDialog Class

```python
class ShareDialog(QDialog):
    """Dialog for generating and sharing temporary URLs."""
    
    def __init__(self, object_name, bucket_name, api_client, parent=None)
    def generate_url(self)
    def copy_url(self)
    def show_qr_code(self)
```

### BucketBrowserDialog Class

```python
class BucketBrowserDialog(QDialog):
    """Dialog for browsing bucket contents and sharing files."""
    
    def __init__(self, bucket_name, api_client, parent=None)
    def load_objects(self)
    def share_single(self, object_name)
    def share_selected(self)
    def show_context_menu(self, position)
```

## License

This implementation is part of the Haio Smart Storage application.
© 2025 Haio Smart Solutions

## Support

For issues or feature requests, please contact the development team or create an issue in the repository.

---

**Document Version**: 1.0  
**Last Updated**: October 7, 2025  
**Author**: GitHub Copilot  
**Status**: ✅ Implementation Complete
