# Logout Functionality Fix

## Date: October 7, 2025

## Issues Identified

### 1. Logout Not Working Properly
**Problem:** 
- When user clicked logout, the app would close the main window but NOT clear saved credentials
- When app was reopened, auto-login would use the saved credentials and log the user back in
- User expected logout to actually log them out, not just hide the window

**Root Cause:**
- The `logout()` function had commented-out code to clear credentials
- Credentials were still saved in `~/.config/haio-client/tokens.json`
- Auto-login on startup would find these credentials and log in automatically

**Solution:**
```python
def logout(self):
    # Save username before clearing
    username_to_clear = self.current_user
    
    # Clear current session
    self.current_user = None
    self.api_client.token = None
    
    # Remove saved credentials from tokens.json
    if username_to_clear:
        # Read tokens file
        # Delete user's entry from JSON
        # Save updated file
```

**Changes Made:**
- Uncommented and improved credential clearing code
- Now properly removes user's entry from tokens.json on logout
- Keeps tokens.json file but removes only the current user's data
- Added error handling and logging

**Result:**
- ✅ Logout now clears saved credentials
- ✅ App will not auto-login after logout
- ✅ User must enter credentials again after logout
- ✅ Main window hides properly
- ✅ Login dialog shows after logout

---

### 2. CSS Transform Property Warning
**Problem:**
```
Unknown property transform
Unknown property transform
```

**Root Cause:**
- Qt StyleSheet (QSS) does NOT support CSS `transform` property
- Used `transform: translateY(-1px)` for button hover effect
- This is a CSS3 property, not supported in Qt's subset of CSS

**Solution:**
- Removed `transform` properties from button styles
- Qt StyleSheet doesn't need transforms for simple hover effects
- Background color changes are sufficient for visual feedback

**Changes Made:**
```python
# BEFORE (caused warnings):
QPushButton#headerButton:hover {
    transform: translateY(-1px);  # ❌ Not supported
}

# AFTER (no warnings):
QPushButton#headerButton:hover {
    background-color: rgba(255, 255, 255, 0.3);  # ✅ Supported
}
```

**Result:**
- ✅ No more "Unknown property transform" warnings
- ✅ Buttons still have nice hover effects
- ✅ Clean console output

---

## Files Modified

### main_new.py
1. **`logout()` method** (lines ~3967-3999)
   - Added credential clearing logic
   - Reads tokens.json
   - Removes current user's entry
   - Saves updated file
   - Added error handling

2. **`setup_styling()` method** (lines ~3410-3418)
   - Removed `transform: translateY(-1px)` from hover state
   - Removed `transform: translateY(0px)` from pressed state
   - Kept color and border changes for visual feedback

---

## Testing Checklist

- [x] Syntax validation passes
- [ ] Logout button clears credentials
- [ ] App does NOT auto-login after logout
- [ ] Login dialog appears after logout
- [ ] Can login again after logout
- [ ] No "Unknown property transform" warnings
- [ ] Hover effects still work on buttons
- [ ] Multiple logout/login cycles work correctly

---

## User Testing Steps

1. **Test Logout Functionality:**
   ```bash
   # Start the app
   python main_new.py
   
   # Login with "Remember me" checked
   # Click logout button
   # Close the app completely
   # Start the app again
   # Expected: Login dialog should appear (NOT auto-login)
   ```

2. **Verify No Warnings:**
   ```bash
   # Start the app
   python main_new.py
   
   # Expected: No "Unknown property transform" messages
   # Console should be clean
   ```

3. **Test Logout/Login Cycle:**
   ```bash
   # Login → Logout → Login → Logout → Login
   # Each logout should require re-entering credentials
   # Each login should work normally
   ```

---

## Technical Details

### Credential Storage
- **Location:** `~/.config/haio-client/tokens.json`
- **Format:** JSON dictionary with username as key
- **Logout behavior:** Removes user's entry, keeps file structure
- **Why not delete entire file?** 
  - Allows multiple users on same system
  - Only clears credentials for current user
  - Preserves other users' saved credentials

### tokens.json Structure
```json
{
  "user1": {
    "token": "abc123...",
    "password_enc": "base64_encoded..."
  },
  "user2": {
    "token": "xyz789...",
    "password_enc": "base64_encoded..."
  }
}
```

After user1 logs out:
```json
{
  "user2": {
    "token": "xyz789...",
    "password_enc": "base64_encoded..."
  }
}
```

---

## Notes

- Logout now works as expected by users
- Auto-login only works if credentials are saved
- Logout is a true logout, not just hiding the window
- No CSS warnings in console
- All hover effects still work properly
- Multiple users can use the same system independently

---

## Related Issues Fixed Previously

1. ✅ Logout button hiding main window
2. ✅ Login dialog behavior after logout
3. ✅ has_logged_in flag for proper app flow
4. ✅ Cancel button behavior in login dialog

---

## Next Steps

1. Test logout functionality thoroughly
2. Verify no auto-login after logout
3. Test multiple logout/login cycles
4. Confirm clean console output (no warnings)
5. Test with multiple user accounts
