#!/usr/bin/env python3
"""
Quick fix for TempURL 401 error
This script will reset the Temp-URL-Key properly
"""

import sys
import os
import secrets
import requests
from PyQt6.QtCore import QSettings

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def reset_tempurl_key():
    """Reset the TempURL key completely."""
    
    print("🔧 TempURL 401 Fix Tool")
    print("=" * 60)
    
    # Get current settings
    settings = QSettings("Haio", "SmartApp")
    old_key = settings.value("temp_url_key")
    
    if old_key:
        print(f"\n❌ Found existing key: {old_key[:10]}...{old_key[-10:]}")
        print("   This key is causing the 401 error")
    else:
        print("\n⚠️  No existing key found")
    
    # Get credentials
    print("\n📝 Please provide your credentials:")
    username = input("   Username: ").strip()
    
    # Try to get token from settings
    token = settings.value(f"token_{username}")
    
    if not token:
        print("   ⚠️  No saved token found")
        token = input("   Auth Token: ").strip()
    else:
        print(f"   ✅ Found saved token: {token[:20]}...")
        use_saved = input("   Use this token? (yes/no): ").strip().lower()
        if use_saved != 'yes' and use_saved != 'y':
            token = input("   Enter new token: ").strip()
    
    base_url = "https://drive.haio.ir"
    
    print("\n🔄 Generating new key...")
    new_key = secrets.token_urlsafe(32)
    print(f"   New key: {new_key[:10]}...{new_key[-10:]}")
    
    print("\n📤 Setting key on server...")
    try:
        headers = {
            'X-Auth-Token': token,
            'X-Account-Meta-Temp-URL-Key': new_key
        }
        storage_url = f"{base_url}/v1/AUTH_{username}"
        
        resp = requests.post(storage_url, headers=headers, timeout=10)
        
        print(f"   Response: {resp.status_code}")
        
        if resp.status_code == 204:
            print("   ✅ Key set successfully on server!")
            
            # Verify it was set
            print("\n🔍 Verifying key on server...")
            verify_resp = requests.head(storage_url, headers={'X-Auth-Token': token}, timeout=10)
            
            found_key = False
            for header, value in verify_resp.headers.items():
                if 'temp-url-key' in header.lower():
                    print(f"   ✅ Found on server: {header}")
                    print(f"      Value: {value[:10]}...{value[-10:]}")
                    found_key = True
            
            if found_key:
                # Save to settings
                print("\n💾 Saving new key to settings...")
                settings.setValue("temp_url_key", new_key)
                print("   ✅ Key saved!")
                
                print("\n" + "=" * 60)
                print("✅ SUCCESS! TempURL should work now")
                print("=" * 60)
                print("\n📋 Next steps:")
                print("   1. Close and restart the application")
                print("   2. Try sharing a file again")
                print("   3. The new URLs should work!")
                
                return True
            else:
                print("\n   ⚠️  Key was set but couldn't verify it")
                print("   Try anyway - save to settings? (yes/no): ", end='')
                if input().strip().lower() in ['yes', 'y']:
                    settings.setValue("temp_url_key", new_key)
                    print("   💾 Saved!")
                    return True
                return False
                
        elif resp.status_code == 401:
            print("   ❌ Authentication failed (401)")
            print("   Your token may be expired or invalid")
            print("\n   Solution:")
            print("   1. Logout from the application")
            print("   2. Login again to get a fresh token")
            print("   3. Run this script again")
            return False
            
        else:
            print(f"   ❌ Unexpected response: {resp.status_code}")
            print(f"   {resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main function."""
    try:
        success = reset_tempurl_key()
        
        if not success:
            print("\n" + "=" * 60)
            print("❌ Fix failed - Manual steps needed:")
            print("=" * 60)
            print("\n1. Close the application")
            print("2. Delete settings file:")
            print("   rm ~/.config/Haio/SmartApp.conf")
            print("3. Start application")
            print("4. Logout and login again")
            print("5. Try sharing again")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
