# 🔗 TempURL Feature - Quick Start Guide

## What is TempURL?

TempURL allows you to create **secure, time-limited links** to share files from your Haio storage without giving away your password or credentials.

## Quick Start in 3 Steps

### Step 1: Open Bucket Browser
Click the **"📂 Browse & Share"** button on any bucket.

### Step 2: Select File
Find the file you want to share in the list.

### Step 3: Generate Link
Click **"🔗 Share"** → Configure options → Click **"Generate Link"** → **Copy** the URL!

## Common Use Cases

### 🎯 Sharing a Document
1. Open bucket browser
2. Find "presentation.pdf"
3. Click Share → Select "24 Hours" → Generate
4. Copy URL and send via email/chat

### 📱 Creating QR Code for Mobile
1. Share a file
2. Generate temporary URL
3. Click **"📱 Show QR Code"**
4. Let others scan with their phone

### 🔒 Restricted Access
1. Share a file
2. Enter recipient's IP address in "IP Restriction"
3. Generate URL
4. Only that IP address can access the file

### 📦 Sharing Multiple Files
1. Open bucket browser
2. Select multiple files (Ctrl+Click)
3. Click **"🔗 Share Selected"**
4. Copy all URLs at once

## Understanding Options

### Duration (How Long Link Works)
- **1 Hour**: Quick, temporary access
- **24 Hours**: Standard sharing (recommended)
- **7 Days**: Week-long access
- **30 Days**: Long-term sharing

### Access Type (What Recipients Can Do)
- **📥 Download Only (GET)**: Can only download (safest)
- **📤 Upload Only (PUT)**: Can only upload
- **🔓 Full Access (POST)**: Can do anything
- **🗑️ Delete Access**: Can delete the file

### IP Restriction (Optional)
- Leave empty: Anyone with link can access
- Enter IP: Only that IP address can use the link
- Example: `192.168.1.100`

## Tips & Tricks

### ✅ Best Practices
- Use shortest duration needed
- Use "Download Only" for most cases
- Add IP restriction for sensitive files
- Check expiration time before sharing

### ⚡ Keyboard Shortcuts
- **Search**: Just start typing in browser
- **Select Multiple**: Ctrl+Click or Shift+Click
- **Right-Click**: Quick access to share options

### 🔍 Finding Files Quickly
Use the search box at top right of browser:
- Type filename or part of it
- Results filter instantly
- Case-insensitive search

## Example URLs

Generated URLs look like this:
```
https://drive.haio.ir/v1/AUTH_user/bucket/file.pdf?
  temp_url_sig=abc123...&
  temp_url_expires=1696723200
```

**Note**: These URLs are long but secure!

## Safety & Security

### ✅ Safe to Share
- Temporary URLs with expiration
- No password or credentials in URL
- Can't be used after expiration

### ⚠️ Be Careful
- URL works for anyone who has it (unless IP restricted)
- Can't revoke URL before expiration
- Shorter durations are more secure

### 🛡️ Security Tips
1. Don't share URLs publicly unless intended
2. Use appropriate access types
3. Monitor expiration times
4. Use IP restrictions for sensitive data

## Troubleshooting

### "TempURL feature not available"
**Fix**: Contact administrator to install required packages

### "Not Authenticated"
**Fix**: Log in first, then try sharing

### Generated URL doesn't work
**Check**:
- Has it expired?
- Is your IP restricted?
- Is internet connection working?

### QR Code not available
**Fix**: Install with: `pip install qrcode[pil]`

## Advanced Features

### Context Menu (Right-Click)
Right-click any file in browser for quick options:
- Share this file
- Copy filename
- Share all selected files

### Bulk Operations
Select many files at once:
1. Click first file
2. Hold Shift and click last file
3. Or Ctrl+Click individual files
4. Click "Share Selected"

### Prefix-Based Sharing
_(Coming in future update)_
Share all files starting with same prefix

## Need Help?

### Common Questions

**Q: How do I know when link expires?**
A: It's shown in the share dialog and when you generate the URL

**Q: Can I extend expiration?**
A: No, generate a new URL instead

**Q: Can multiple people use same URL?**
A: Yes, unless IP restricted

**Q: What happens after expiration?**
A: Link stops working immediately

**Q: Can I see who used my link?**
A: Not currently available

### Getting Support
- Check error messages carefully
- Try refreshing the browser
- Contact support team
- Check documentation

## Video Tutorial
_(Coming soon)_

## What's Next?

Planned features:
- URL history tracking
- Email sharing integration
- Usage analytics
- Bulk operations improvements

---

**Quick Reference Card**

| Action | Button | Location |
|--------|--------|----------|
| Open Browser | 📂 Browse & Share | Bucket widget |
| Share File | 🔗 Share | File row |
| Copy URL | 📋 Copy | After generation |
| QR Code | 📱 Show QR Code | After generation |
| Search | 🔍 | Browser top right |

---

**Last Updated**: October 7, 2025  
**Version**: 1.0  
**Status**: ✅ Feature Active
