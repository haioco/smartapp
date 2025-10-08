# TempURL 401 Error - Diagnosis and Fixes

## 🐛 Problem

When sharing files via TempURL, users get a **401 Unauthorized** error when accessing the generated URL.

## 🔍 Root Cause

The 401 error occurs because:

1. **Temp-URL-Key mismatch**: The key used to generate the signature doesn't match the key stored on the server
2. **Key not set on server**: The `X-Account-Meta-Temp-URL-Key` header was never successfully set
3. **Token expired**: The authentication token used to set the key has expired
4. **Server doesn't support TempURL**: The Swift/S3 server configuration may have TempURL disabled

## 🔧 Solutions

### Solution 1: Reset the Temp-URL-Key (Recommended)

**For Users:**
1. Close the application completely
2. Delete the settings file:
   ```bash
   # Linux
   rm ~/.config/Haio/SmartApp.conf
   
   # Windows
   # Delete: C:\Users\YourName\AppData\Roaming\Haio\SmartApp.conf
   ```
3. Restart the application
4. Login again (this refreshes your auth token)
5. Try sharing a file again (this will generate and set a new key)

**Why this works:**
- Removes any mismatched or corrupted keys
- Forces generation of a fresh key
- Fresh login provides valid authentication token
- Key is properly set on server with valid token

### Solution 2: Manual Key Reset via Diagnostic Tool

Run the diagnostic tool to test and fix:

```bash
cd /home/devcloud/Documents/mine/haio/smarthaioapp/client
python tests/test_tempurl_diagnostic.py
```

The tool will:
- Test if the key is set on the server
- Generate a test TempURL
- Test if the URL works
- Show detailed error information

### Solution 3: Check Server Configuration

Contact your Haio admin to verify:

```bash
# Server-side check (admin only)
swift stat -v AUTH_username
```

Look for:
- `X-Account-Meta-Temp-Url-Key: <key>`
- `X-Account-Meta-Temp-Url-Key-2: <key2>` (if using secondary key)

If not present, TempURL might be disabled on server.

## 🔍 How to Diagnose

### Step 1: Check if Key Exists Locally

```python
# Linux
cat ~/.config/Haio/SmartApp.conf | grep temp_url_key

# Or in Python
from PyQt6.QtCore import QSettings
settings = QSettings("Haio", "SmartApp")
print(settings.value("temp_url_key"))
```

### Step 2: Test if Key is Set on Server

```bash
curl -i -H "X-Auth-Token: YOUR_TOKEN" \
  https://drive.haio.ir/v1/AUTH_USERNAME
```

Look for `X-Account-Meta-Temp-Url-Key` in response headers.

### Step 3: Test Generated URL

```bash
curl -I "YOUR_TEMPURL"
```

Expected responses:
- **200**: ✅ URL works!
- **401**: ❌ Key mismatch or not set
- **404**: File doesn't exist
- **410**: URL expired

## 💡 Prevention

### For Developers:

**Improved Error Handling in `share_dialog.py`:**

```python
def _get_or_create_temp_url_key(self) -> str:
    """Get existing or create new temp URL key with proper error handling."""
    settings = QSettings("Haio", "SmartApp")
    key = settings.value("temp_url_key", None)
    
    if not key:
        key = secrets.token_urlsafe(32)
        settings.setValue("temp_url_key", key)
        
        # Set on server with retry logic
        username = self.api_client.username
        temp_manager = TempURLManager(self.api_client, key)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                success = temp_manager.set_temp_url_key(username, key)
                if success:
                    print("✅ Temp-URL-Key set successfully")
                    break
                elif attempt == max_retries - 1:
                    # Last attempt failed
                    QMessageBox.critical(
                        self,
                        "TempURL Setup Failed",
                        "Could not set temporary URL key on server.\n\n"
                        "This may happen if:\n"
                        "• Your session has expired (try logging out and back in)\n"
                        "• The server doesn't support TempURL feature\n"
                        "• Network connectivity issues\n\n"
                        "Please logout, login again, and retry."
                    )
            except Exception as e:
                if attempt == max_retries - 1:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to configure TempURL: {str(e)}"
                    )
    
    return key
```

**Add Key Verification:**

```python
def verify_temp_url_key_on_server(self) -> bool:
    """Verify that the server has the temp URL key."""
    try:
        username = self.api_client.username
        storage_url = f"{self.api_client.base_url}/v1/AUTH_{username}"
        headers = {'X-Auth-Token': self.api_client.token}
        
        resp = requests.head(storage_url, headers=headers, timeout=10)
        
        # Check if temp-url-key header exists
        for header in resp.headers:
            if 'temp-url-key' in header.lower():
                return True
        
        return False
    except:
        return False
```

### For Users:

**Before Sharing:**
1. Make sure you're logged in (token is fresh)
2. If you get 401, logout and login again
3. Try sharing again (first share after login will set the key)

**If 401 Persists:**
1. Delete settings file
2. Restart app
3. Login fresh
4. Generate new share link

## 📊 Technical Details

### How TempURL Works:

1. **Key Generation:**
   ```python
   key = secrets.token_urlsafe(32)  # Generate secure random key
   ```

2. **Set on Server:**
   ```http
   POST /v1/AUTH_username HTTP/1.1
   X-Auth-Token: <token>
   X-Account-Meta-Temp-URL-Key: <key>
   ```

3. **Generate Signature:**
   ```python
   hmac_body = f"{method}\n{expires}\n{path}"
   signature = hmac.new(key.encode(), hmac_body.encode(), sha1).hexdigest()
   ```

4. **Build URL:**
   ```
   https://drive.haio.ir/v1/AUTH_username/bucket/file.pdf
     ?temp_url_sig=<signature>
     &temp_url_expires=<timestamp>
   ```

5. **Server Validates:**
   - Server retrieves its stored `X-Account-Meta-Temp-URL-Key`
   - Recalculates signature using same method
   - Compares signatures
   - If match → 200 OK
   - If mismatch → 401 Unauthorized

### Why 401 Happens:

```
Client Key (local):  abc123def456...
Server Key:          xyz789ghi012...   ❌ MISMATCH!
```

When keys don't match, signatures will never match → 401

## 🎯 Quick Fix Checklist

- [ ] Close application
- [ ] Delete `~/.config/Haio/SmartApp.conf`
- [ ] Start application
- [ ] Login fresh
- [ ] Try sharing file
- [ ] If still 401:
  - [ ] Run diagnostic tool
  - [ ] Check server logs
  - [ ] Contact Haio support

## 📝 For Future Development

### Add to v2.0.1:

1. **Automatic Key Sync Detection**
   - Verify key on server matches local key
   - Auto-reset if mismatch detected

2. **Better Error Messages**
   - Tell user exactly what went wrong
   - Provide one-click fix options

3. **Key Rotation**
   - Allow users to regenerate key
   - Add "Reset TempURL Key" button in settings

4. **Health Check**
   - Test TempURL before showing share dialog
   - Warn user if setup incomplete

## 🔗 Related Files

- `src/features/tempurl_manager.py` - TempURL generation logic
- `src/ui/dialogs/share_dialog.py` - Share dialog UI
- `tests/test_tempurl_diagnostic.py` - Diagnostic tool
- `tests/test_tempurl.py` - Unit tests

## 📞 Support

If none of these solutions work:
1. Run the diagnostic tool and save output
2. Check application logs
3. Contact Haio support with:
   - Diagnostic tool output
   - Error screenshots
   - Steps to reproduce

---

**Issue**: TempURL 401 Unauthorized  
**Severity**: High (feature doesn't work)  
**Status**: Workaround available, permanent fix pending v2.0.1  
**Updated**: October 8, 2025
