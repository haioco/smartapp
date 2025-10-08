# Service Removal Error Handling Fix

## Issue Fixed

**Problem**: When user cancels password prompt during auto-mount service removal:
- Error: "Failed to remove auto-mount service for {bucket}"
- Bucket deleted in console but service remains on system
- May cause boot errors when system tries to mount deleted bucket
- No clear guidance on how to fix

**Scenario**:
1. Bucket deleted in Haio console
2. App detects deletion (within 60s)
3. App asks for password to remove systemd service
4. **User cancels password prompt** (by mistake or intentionally)
5. Service remains on system → Boot errors later

---

## Solutions Implemented

### 1. Graceful Password Cancellation Handling

**File**: `main_new.py`

#### Updated: `remove_systemd_service()` (Line ~1185)

**Before**:
```python
if password_dialog.exec() != QDialog.DialogCode.Accepted:
    return False  # ❌ Silent failure, no explanation
```

**After**:
```python
password_dialog = PasswordDialog(
    parent_widget, 
    f"System password required to remove auto-mount service for '{bucket_name}'.\n\n"
    f"Note: If you cancel, the service will remain on your system.\n"  # ✅ Clear warning
    f"You can remove it manually later if needed."
)

if password_dialog.exec() != QDialog.DialogCode.Accepted:
    print(f"⚠️  User cancelled password prompt for removing service: {service_name}")
    return False  # ✅ Logged reason
```

**Improvements**:
- ✅ Clear warning in password dialog
- ✅ Console logging when cancelled
- ✅ User knows consequences

---

### 2. User-Friendly Error Message on Failure

**File**: `main_new.py` (Line ~4228)

#### Updated: `sync_bucket_stats()` deletion handling

**After**:
```python
success = self.rclone_manager.remove_auto_mount_service(...)
if success:
    print(f"✅ Successfully removed auto-mount service for {bucket_name}")
else:
    print(f"⚠️  Failed to remove auto-mount service for {bucket_name}")
    
    # ✅ Show detailed warning dialog
    from PyQt6.QtWidgets import QMessageBox
    service_name = f"haio-{self.current_user}-{bucket_name}"
    QMessageBox.warning(
        self,
        "Service Removal Failed",
        f"Could not remove auto-mount service for '{bucket_name}'.\n\n"
        f"The bucket was deleted in the console, but the auto-mount service "
        f"remains on your system. This may cause errors on next boot.\n\n"
        f"To remove it manually, run:\n"
        f"  sudo systemctl disable {service_name}.service\n"
        f"  sudo systemctl stop {service_name}.service\n"
        f"  sudo rm /etc/systemd/system/{service_name}.service\n"
        f"  sudo systemctl daemon-reload\n\n"
        f"Or disable auto-mount for this bucket before deleting it."
    )
```

**Benefits**:
- ✅ Clear explanation of the problem
- ✅ Exact commands to fix manually
- ✅ Advice for future (disable auto-mount first)
- ✅ Bucket still removed from UI (doesn't block)

---

### 3. Better Command Execution Logging

**File**: `main_new.py` (Line ~1218)

**Before**:
```python
for cmd in commands:
    subprocess.run(cmd, shell=True, capture_output=True, text=True)
    # Continue even if some commands fail
```

**After**:
```python
commands = [
    (f'echo "{password}" | sudo -S systemctl disable "{service_name}"', "Disabling service"),
    (f'echo "{password}" | sudo -S systemctl stop "{service_name}"', "Stopping service"),
    (f'echo "{password}" | sudo -S rm -f "{self.service_dir}/{service_name}"', "Removing service file"),
    (f'echo "{password}" | sudo -S systemctl daemon-reload', "Reloading systemd")
]

all_success = True
for cmd, description in commands:
    print(f"  {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    if result.returncode != 0 and result.stderr:
        # Check if it's just "not found" error
        if 'No such file' not in result.stderr and 'not loaded' not in result.stderr:
            print(f"    ⚠️  {description} failed: {result.stderr.strip()}")
            all_success = False
        else:
            print(f"    ℹ️  {description}: Service already removed")
    else:
        print(f"    ✅ {description} completed")

return all_success
```

**Benefits**:
- ✅ Step-by-step progress logging
- ✅ Distinguishes between real errors and "already removed"
- ✅ Returns success/failure status accurately
- ✅ Timeout protection (10s per command)

---

### 4. Manual Cleanup Script

**New File**: `cleanup_services.sh`

Standalone bash script to clean up leftover services:

```bash
#!/bin/bash
# Scan for Haio auto-mount services
# Offer to remove them interactively
# Handle both user and system services

./cleanup_services.sh
```

**Features**:
- 🔍 Scans `~/.config/systemd/user/` for user services
- 🔍 Scans `/etc/systemd/system/` for system services
- 📋 Lists all found services with status (enabled/disabled)
- 🧹 Removes services interactively or with confirmation
- ✅ Handles both user and system services
- 📝 Shows summary of removed/failed services

**Example Output**:
```
============================================================
Haio Smart App - Manual Auto-Mount Service Cleanup
============================================================

🔍 Scanning for Haio auto-mount services...

📋 Found 2 Haio service(s):

  1. [user] haio-user-mybucket.service
      Status: 🟢 Enabled
  2. [system] haio-user-mydoc2.service
      Status: 🔴 Disabled

============================================================
Would you like to remove these services?
============================================================

Remove all services? [y/N]: y

🧹 Removing services...

Removing [user] haio-user-mybucket.service...
  ✅ Removed successfully
Removing [system] haio-user-mydoc2.service...
  ✅ Removed successfully

Reloading systemd...

============================================================
Cleanup Summary
============================================================
  ✅ Removed: 2 service(s)
  ❌ Failed:  0 service(s)

🎉 All services removed successfully!
```

---

## User Experience Flow

### Scenario A: User Provides Password

```
Bucket deleted in console
  ↓
App detects (within 60s)
  ↓
Password dialog: "System password required to remove auto-mount service..."
  ↓
User enters password ✅
  ↓
Console:
  Disabling service...
    ✅ Disabling service completed
  Stopping service...
    ✅ Stopping service completed
  Removing service file...
    ✅ Removing service file completed
  Reloading systemd...
    ✅ Reloading systemd completed
  ↓
✅ Successfully removed auto-mount service
  ↓
Bucket removed from UI
  ↓
Status: "✓ Removed 1 deleted bucket(s)"
```

---

### Scenario B: User Cancels Password

```
Bucket deleted in console
  ↓
App detects (within 60s)
  ↓
Password dialog: 
  "System password required to remove auto-mount service for 'mybucket'.
   
   Note: If you cancel, the service will remain on your system.
   You can remove it manually later if needed."
  ↓
User clicks Cancel ❌
  ↓
Console:
  ⚠️  User cancelled password prompt for removing service: haio-user-mybucket.service
  ⚠️  Failed to remove auto-mount service for mybucket
  ↓
Warning Dialog:
  "Service Removal Failed
   
   Could not remove auto-mount service for 'mybucket'.
   
   The bucket was deleted in the console, but the auto-mount service
   remains on your system. This may cause errors on next boot.
   
   To remove it manually, run:
     sudo systemctl disable haio-user-mybucket.service
     sudo systemctl stop haio-user-mybucket.service
     sudo rm /etc/systemd/system/haio-user-mybucket.service
     sudo systemctl daemon-reload
   
   Or disable auto-mount for this bucket before deleting it."
  ↓
User clicks OK
  ↓
Bucket removed from UI ✅ (doesn't block removal)
  ↓
Status: "✓ Removed 1 deleted bucket(s)"
  ↓
Later: User runs cleanup script or manual commands
```

---

## Manual Cleanup Options

### Option 1: Use Cleanup Script (Easiest)

```bash
cd /path/to/haio/smarthaioapp/client
./cleanup_services.sh
```

Interactive, scans and removes all Haio services.

---

### Option 2: Manual Commands (Expert)

```bash
# List services
systemctl --user list-units | grep haio
sudo systemctl list-units | grep haio

# Remove specific service
SERVICE_NAME="haio-user-mybucket.service"

# If it's a user service:
systemctl --user disable $SERVICE_NAME
systemctl --user stop $SERVICE_NAME
rm ~/.config/systemd/user/$SERVICE_NAME
systemctl --user daemon-reload

# If it's a system service:
sudo systemctl disable $SERVICE_NAME
sudo systemctl stop $SERVICE_NAME
sudo rm /etc/systemd/system/$SERVICE_NAME
sudo systemctl daemon-reload
```

---

### Option 3: Disable Auto-Mount First (Prevention)

**Before deleting bucket in console**:
1. Open Haio Smart App
2. Find the bucket
3. Uncheck "Auto-mount at boot"
4. Wait for confirmation
5. Now delete bucket in console
6. No cleanup needed! ✅

---

## Error Messages Reference

### Console Output

| Message | Meaning | Action |
|---------|---------|--------|
| `⚠️ User cancelled password prompt` | Password dialog cancelled | Use cleanup script later |
| `⚠️ No password provided` | Empty password submitted | Try again or cleanup later |
| `❌ Timeout while removing service` | Command took >10s | Check system, try cleanup script |
| `✅ Successfully removed auto-mount service` | All good! | No action needed |
| `⚠️ Failed to remove auto-mount service` | Error occurred | See warning dialog |

### GUI Dialogs

| Dialog | Trigger | Purpose |
|--------|---------|---------|
| Password Dialog | Service removal needed | Get sudo password |
| Warning Dialog | Service removal failed | Explain issue + manual fix |
| Status Bar | After cleanup | Confirm completion |

---

## Best Practices

### For Users

1. **✅ DO**: Enter password when prompted
2. **✅ DO**: Disable auto-mount before deleting buckets
3. **✅ DO**: Use cleanup script if you cancelled by mistake
4. **❌ DON'T**: Ignore the warning dialog
5. **❌ DON'T**: Delete buckets without disabling auto-mount

### For Developers

1. **✅ DO**: Always show clear error messages
2. **✅ DO**: Provide manual fix instructions
3. **✅ DO**: Log cancellations and errors
4. **✅ DO**: Continue with bucket removal even if service fails
5. **❌ DON'T**: Block bucket removal due to service error

---

## Testing Scenarios

### Test 1: Cancel Password Prompt
```bash
# 1. Enable auto-mount for a bucket
# 2. Delete bucket in Haio console
# 3. Wait 60s for app to detect
# 4. When password dialog appears, click Cancel
# Expected: Warning dialog with manual commands
```

### Test 2: Wrong Password
```bash
# 1. Enable auto-mount for a bucket
# 2. Delete bucket in Haio console
# 3. Wait 60s for app to detect
# 4. Enter wrong password
# Expected: Commands fail, warning dialog shown
```

### Test 3: Successful Removal
```bash
# 1. Enable auto-mount for a bucket
# 2. Delete bucket in Haio console
# 3. Wait 60s for app to detect
# 4. Enter correct password
# Expected: Service removed, no warning, success message
```

### Test 4: Manual Cleanup Script
```bash
# 1. Have leftover services (from cancelled password)
# 2. Run: ./cleanup_services.sh
# 3. Confirm removal
# Expected: All services removed, summary shown
```

---

## Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `main_new.py` | Lines ~1185, ~4228 | Better error handling |

## Files Created

| File | Purpose |
|------|---------|
| `cleanup_services.sh` | Manual service cleanup script |

---

## Summary

**Problem**: Cancelled password → Silent failure → Boot errors later

**Solution**: 
1. ✅ Clear warning in password dialog
2. ✅ Detailed error message with fix instructions
3. ✅ Bucket still removed from UI (doesn't block)
4. ✅ Cleanup script for manual removal
5. ✅ Better logging throughout

**User Impact**: 🌟 Clear guidance, no confusion, easy fixes

---

**Date**: October 7, 2025  
**Component**: Service removal error handling  
**Result**: ✅ User-friendly error handling with multiple recovery options!
