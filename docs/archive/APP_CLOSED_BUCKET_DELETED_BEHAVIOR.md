# App Closed During Bucket Deletion - Behavior Analysis

## Configuration Change

✅ **Auto-refresh interval changed**: 60s → **30s**

**File**: `main_new.py` line 3166
```python
# Before
self.stats_sync_timer.setInterval(60000)  # 60 seconds

# After  
self.stats_sync_timer.setInterval(30000)  # 30 seconds
```

---

## Question: What happens if app is closed and bucket deleted?

### Scenario Timeline

```
Time 0s:   User has app open with 5 buckets
           Bucket "mydoc" is mounted at /home/user/haio-user-mydoc

Time 10s:  User closes the app
           Mount remains active (rclone process still running)

Time 30s:  User deletes "mydoc" bucket in Haio console
           (App is closed, doesn't know about deletion)

Time 60s:  User reopens the app
           What happens? ↓
```

---

## Detailed Flow: App Startup After Bucket Deletion

### Step 1: App Starts & Loads Buckets

```python
def load_buckets(self):
    # Calls API: list_containers()
    # Gets current buckets from server
```

**Result**: API returns **4 buckets** (mydoc is deleted)

---

### Step 2: Display Buckets

```python
def display_buckets(self):
    # Clear old widgets
    # Create widgets ONLY for buckets from API
    
    for bucket in self.buckets:  # Only 4 buckets now
        widget = BucketWidget(bucket, ...)
```

**Result**: UI shows only **4 bucket widgets** (mydoc widget not created)

---

### Step 3: Scan Existing Mounts

```python
def scan_existing_mounts(self):
    # Check each widget's mount point
    for widget in self.bucket_widgets:  # Only 4 widgets
        if self.rclone_manager.is_mounted(widget.mount_point):
            widget.is_mounted = True
```

**Problem**: The deleted bucket "mydoc" has no widget to check!

**Result**: 
- ✅ The 4 existing buckets are checked
- ❌ The "mydoc" mount is **not checked** (no widget exists for it)
- ❌ The "mydoc" mount **remains active** in background

---

### Step 4: What User Sees

```
┌─────────────────────────────────────┐
│  Haio Smart App                     │
├─────────────────────────────────────┤
│  [Bucket 1] [Mount]                 │
│  [Bucket 2] [Mount]  ✅ Mounted     │
│  [Bucket 3] [Mount]                 │
│  [Bucket 4] [Mount]                 │
│                                     │
│  (mydoc is NOT shown)               │
└─────────────────────────────────────┘
```

**BUT**: The "mydoc" mount is **still active** in the system!

```bash
$ ls /home/user/haio-user-mydoc
# Still accessible! rclone process still running!
```

---

## Problem: Orphaned Mount

### Current Behavior (Without Fix)

1. ❌ User sees: 4 buckets in app
2. ❌ System has: 5 mounts (including deleted bucket)
3. ❌ Result: **Orphaned mount** that app doesn't know about
4. ❌ User can't unmount it from app (no widget)
5. ❌ Manual cleanup needed

### Why It Happens

```
App Startup Flow:
  1. Load buckets from API (4 buckets)
  2. Create widgets (4 widgets)
  3. Scan mounts for existing widgets (4 widgets checked)
  4. Deleted bucket mount (5th mount) is NEVER checked!
```

**Root Cause**: `scan_existing_mounts()` only checks widgets, not actual system mounts.

---

## Solution: Detect & Cleanup Orphaned Mounts

I'll add a comprehensive mount scan that detects orphaned mounts and offers to clean them up.

### Implementation Plan

```python
def scan_existing_mounts(self):
    # 1. Check widgets (existing behavior)
    for widget in self.bucket_widgets:
        if is_mounted(widget.mount_point):
            widget.is_mounted = True
    
    # 2. NEW: Find all Haio mounts in system
    all_haio_mounts = find_all_haio_mounts()
    
    # 3. NEW: Find orphaned mounts (in system but not in widgets)
    widget_mount_points = {w.mount_point for w in self.bucket_widgets}
    orphaned_mounts = all_haio_mounts - widget_mount_points
    
    # 4. NEW: Offer to cleanup orphaned mounts
    if orphaned_mounts:
        show_orphaned_mount_dialog(orphaned_mounts)
```

### Detection Logic

```python
def find_all_haio_mounts():
    """Find all Haio mount points on the system."""
    home = os.path.expanduser("~")
    haio_mounts = []
    
    # Look for all haio-* directories in home
    for item in os.listdir(home):
        if item.startswith("haio-"):
            path = os.path.join(home, item)
            # Check if it's actually mounted
            if is_mounted(path):
                haio_mounts.append(path)
    
    return set(haio_mounts)
```

---

## Proposed User Experience

### Scenario A: No Orphaned Mounts (Normal)

```
App starts → Load buckets → Show buckets → All good ✅
```

---

### Scenario B: Orphaned Mounts Detected

```
App starts
  ↓
Load buckets (4 buckets from API)
  ↓
Detect orphaned mounts (1 mount)
  ↓
Show Dialog:

┌──────────────────────────────────────────────┐
│  Orphaned Mounts Detected                    │
├──────────────────────────────────────────────┤
│                                              │
│  Found 1 mount(s) for buckets that no       │
│  longer exist:                               │
│                                              │
│    • mydoc                                   │
│      at /home/user/haio-user-mydoc           │
│                                              │
│  These buckets were likely deleted while    │
│  the app was closed.                        │
│                                              │
│  Would you like to unmount them now?        │
│                                              │
│  [ Unmount All ]  [ Keep Them ]  [ Details ]│
└──────────────────────────────────────────────┘
```

**If user clicks "Unmount All"**:
```
Unmounting mydoc...
✓ Successfully unmounted mydoc
✓ Cleaned up 1 orphaned mount(s)
```

**If user clicks "Keep Them"**:
```
Orphaned mounts will remain active.
You can access them manually or use the cleanup tool.
```

**If user clicks "Details"**:
```
Shows list of mount points with commands to manually unmount
```

---

## Implementation

Let me implement this fix:

```python
def scan_existing_mounts(self):
    """Scan for existing mounts and detect orphaned mounts."""
    
    # Step 1: Check widgets for their mounts (existing behavior)
    for widget in self.bucket_widgets:
        if hasattr(widget, 'mount_point') and widget.mount_point:
            if self.rclone_manager.is_mounted(widget.mount_point):
                widget.is_mounted = True
                widget.update_mount_status()
    
    # Step 2: NEW - Detect orphaned mounts
    orphaned = self.detect_orphaned_mounts()
    if orphaned:
        self.handle_orphaned_mounts(orphaned)

def detect_orphaned_mounts(self) -> List[str]:
    """Find mounts for buckets that no longer exist."""
    # Get all Haio mount points in home directory
    home = os.path.expanduser("~")
    all_mounts = []
    
    try:
        for item in os.listdir(home):
            if item.startswith(f"haio-{self.current_user}-"):
                path = os.path.join(home, item)
                if self.rclone_manager.is_mounted(path):
                    all_mounts.append(path)
    except Exception as e:
        print(f"Error scanning for orphaned mounts: {e}")
        return []
    
    # Get mount points from current widgets
    widget_mounts = {w.mount_point for w in self.bucket_widgets 
                     if hasattr(w, 'mount_point')}
    
    # Find orphaned (mounted but no widget)
    orphaned = [m for m in all_mounts if m not in widget_mounts]
    return orphaned

def handle_orphaned_mounts(self, orphaned: List[str]):
    """Show dialog and offer to cleanup orphaned mounts."""
    bucket_names = [os.path.basename(m).replace(f"haio-{self.current_user}-", "") 
                    for m in orphaned]
    
    msg = QMessageBox(self)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("Orphaned Mounts Detected")
    msg.setText(f"Found {len(orphaned)} mount(s) for deleted buckets:")
    msg.setInformativeText(
        f"Buckets: {', '.join(bucket_names)}\n\n"
        f"These buckets were likely deleted while the app was closed.\n\n"
        f"Would you like to unmount them now?"
    )
    
    unmount_all_btn = msg.addButton("Unmount All", QMessageBox.ButtonRole.AcceptRole)
    keep_btn = msg.addButton("Keep Them", QMessageBox.ButtonRole.RejectRole)
    
    msg.exec()
    
    if msg.clickedButton() == unmount_all_btn:
        self.cleanup_orphaned_mounts(orphaned)

def cleanup_orphaned_mounts(self, orphaned: List[str]):
    """Unmount orphaned mounts."""
    for mount_point in orphaned:
        bucket_name = os.path.basename(mount_point).replace(f"haio-{self.current_user}-", "")
        print(f"Unmounting orphaned bucket: {bucket_name}")
        success, msg = self.rclone_manager.unmount_bucket(mount_point)
        if success:
            print(f"✅ Unmounted {bucket_name}")
        else:
            print(f"⚠️ Failed to unmount {bucket_name}: {msg}")
```

---

## Benefits

1. ✅ **Auto-detection**: Finds orphaned mounts on startup
2. ✅ **User choice**: Ask before unmounting
3. ✅ **Clean system**: No leftover mounts
4. ✅ **Clear feedback**: Shows what was found and cleaned
5. ✅ **Fallback**: User can keep mounts if needed

---

## Summary

### Current Behavior (Without Fix)
```
App closed → Bucket deleted → App reopened
Result: ❌ Orphaned mount, manual cleanup needed
```

### With Fix
```
App closed → Bucket deleted → App reopened
Result: ✅ Detects orphan, offers cleanup, system clean
```

### Configuration
- ✅ Auto-refresh: **30 seconds** (was 60s)
- ✅ Orphan detection: **On startup**
- ✅ User control: **Dialog with choices**

---

**Status**: Ready to implement orphaned mount detection!

Would you like me to implement this fix?
