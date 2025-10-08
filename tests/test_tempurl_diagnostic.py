#!/usr/bin/env python3
"""
TempURL Diagnostic Tool
Helps diagnose and fix TempURL 401 errors
"""

import sys
import os
import hmac
from hashlib import sha1
from time import time
import requests

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_temp_url_key_set(base_url, token, username, temp_url_key):
    """Test if the Temp-URL-Key is set on the server."""
    print(f"\n{'='*70}")
    print("Testing Temp-URL-Key Configuration")
    print(f"{'='*70}")
    
    # Try to set the key
    print(f"\n1. Setting Temp-URL-Key on server...")
    print(f"   Base URL: {base_url}")
    print(f"   Username: {username}")
    print(f"   Key length: {len(temp_url_key)} chars")
    
    try:
        headers = {
            'X-Auth-Token': token,
            'X-Account-Meta-Temp-URL-Key': temp_url_key
        }
        storage_url = f"{base_url}/v1/AUTH_{username}"
        
        print(f"   POST to: {storage_url}")
        resp = requests.post(storage_url, headers=headers, timeout=10)
        
        print(f"   Response code: {resp.status_code}")
        
        if resp.status_code == 204:
            print("   ✅ Temp-URL-Key set successfully!")
            return True
        elif resp.status_code == 401:
            print("   ❌ Authentication failed (401)")
            print("   → Token may be expired or invalid")
            return False
        elif resp.status_code == 403:
            print("   ❌ Permission denied (403)")
            print("   → Account may not have permission to set metadata")
            return False
        else:
            print(f"   ❌ Unexpected response: {resp.status_code}")
            print(f"   → {resp.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_temp_url_generation(base_url, username, bucket_name, object_name, temp_url_key):
    """Generate and test a TempURL."""
    print(f"\n{'='*70}")
    print("Testing TempURL Generation")
    print(f"{'='*70}")
    
    # Generate URL
    print(f"\n2. Generating TempURL...")
    print(f"   Bucket: {bucket_name}")
    print(f"   Object: {object_name}")
    
    method = 'GET'
    duration_seconds = 3600
    expires = int(time() + duration_seconds)
    
    path = f"/v1/AUTH_{username}/{bucket_name}/{object_name}"
    hmac_body = f"{method}\n{expires}\n{path}"
    
    signature = hmac.new(
        temp_url_key.encode(),
        hmac_body.encode(),
        sha1
    ).hexdigest()
    
    temp_url = f"{base_url}{path}?temp_url_sig={signature}&temp_url_expires={expires}"
    
    print(f"   Path: {path}")
    print(f"   Expires: {expires}")
    print(f"   Signature: {signature}")
    print(f"\n   Generated URL:")
    print(f"   {temp_url}")
    
    return temp_url

def test_temp_url_access(temp_url):
    """Test if the TempURL works."""
    print(f"\n{'='*70}")
    print("Testing TempURL Access")
    print(f"{'='*70}")
    
    print(f"\n3. Testing URL access...")
    
    try:
        # Try HEAD request first (doesn't download content)
        resp = requests.head(temp_url, timeout=10, allow_redirects=True)
        
        print(f"   Response code: {resp.status_code}")
        
        if resp.status_code == 200:
            print("   ✅ TempURL works! File is accessible")
            if 'content-length' in resp.headers:
                size = int(resp.headers['content-length'])
                print(f"   File size: {size:,} bytes")
            return True
        elif resp.status_code == 401:
            print("   ❌ Unauthorized (401)")
            print("   \n   Possible causes:")
            print("   → Temp-URL-Key not set on server")
            print("   → Wrong Temp-URL-Key used for signature")
            print("   → Signature calculation mismatch")
            print("\n   Solutions:")
            print("   1. Logout and login again to refresh token")
            print("   2. Delete temp_url_key from settings and regenerate")
            print("   3. Check if server supports TempURL feature")
            return False
        elif resp.status_code == 404:
            print("   ❌ Not found (404)")
            print("   → File doesn't exist or path is wrong")
            return False
        elif resp.status_code == 410:
            print("   ❌ URL expired (410)")
            print("   → The TempURL has expired")
            return False
        else:
            print(f"   ❌ Unexpected response: {resp.status_code}")
            print(f"   → {resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error accessing URL: {e}")
        return False

def get_account_metadata(base_url, token, username):
    """Check current account metadata."""
    print(f"\n{'='*70}")
    print("Checking Account Metadata")
    print(f"{'='*70}")
    
    print(f"\n4. Checking current Temp-URL-Key on server...")
    
    try:
        headers = {'X-Auth-Token': token}
        storage_url = f"{base_url}/v1/AUTH_{username}"
        
        resp = requests.head(storage_url, headers=headers, timeout=10)
        
        print(f"   Response code: {resp.status_code}")
        
        if resp.status_code == 204 or resp.status_code == 200:
            # Check for Temp-URL-Key in headers
            temp_key_header = None
            for header, value in resp.headers.items():
                if 'temp-url-key' in header.lower():
                    temp_key_header = value
                    print(f"   ✅ Found: {header} = {value[:10]}...{value[-10:]}")
            
            if not temp_key_header:
                print("   ⚠️  No Temp-URL-Key found in account metadata")
                print("   → Key needs to be set on server")
                return False
            return True
        else:
            print(f"   ❌ Failed to get metadata: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run diagnostic."""
    print(f"\n{'='*70}")
    print("Haio Smart Storage - TempURL Diagnostic Tool")
    print(f"{'='*70}")
    
    # Get configuration from user
    base_url = input("\nEnter base URL (default: https://drive.haio.ir): ").strip() or "https://drive.haio.ir"
    token = input("Enter auth token: ").strip()
    username = input("Enter username: ").strip()
    bucket_name = input("Enter bucket name to test: ").strip()
    object_name = input("Enter object name to test: ").strip()
    
    # Get or generate temp URL key
    print("\n" + "="*70)
    key_choice = input("Use existing key or generate new? (existing/new): ").strip().lower()
    
    if key_choice == 'new':
        import secrets
        temp_url_key = secrets.token_urlsafe(32)
        print(f"Generated new key: {temp_url_key}")
    else:
        temp_url_key = input("Enter existing temp_url_key: ").strip()
    
    # Run tests
    print(f"\n{'='*70}")
    print("Starting Diagnostic Tests")
    print(f"{'='*70}")
    
    # Test 1: Set key on server
    key_set = test_temp_url_key_set(base_url, token, username, temp_url_key)
    
    # Test 2: Check if key is actually set
    if key_set:
        get_account_metadata(base_url, token, username)
    
    # Test 3: Generate TempURL
    temp_url = test_temp_url_generation(base_url, username, bucket_name, object_name, temp_url_key)
    
    # Test 4: Test access
    if temp_url:
        test_temp_url_access(temp_url)
    
    print(f"\n{'='*70}")
    print("Diagnostic Complete")
    print(f"{'='*70}")
    
    print("\n📋 Summary of findings:")
    print("   1. Check if Temp-URL-Key was set successfully (step 1)")
    print("   2. Verify key exists in account metadata (step 4)")
    print("   3. If URL returns 401, the server key doesn't match local key")
    print("\n💡 Tips:")
    print("   - If 401 persists, delete ~/.config/Haio/SmartApp.conf")
    print("   - Logout and login to refresh token")
    print("   - Verify server supports TempURL (some Swift configs disable it)")

if __name__ == "__main__":
    main()
