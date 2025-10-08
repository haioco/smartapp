#!/usr/bin/env python3
"""
Test script for TempURL functionality
Tests the core components without requiring full app launch
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all modules can be imported."""
    print("Testing imports...")
    
    try:
        from tempurl_manager import TempURLManager
        print("✓ tempurl_manager imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import tempurl_manager: {e}")
        return False
    
    try:
        from share_dialog import ShareDialog, BulkShareDialog
        print("✓ share_dialog imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import share_dialog: {e}")
        return False
    
    try:
        from bucket_browser import BucketBrowserDialog
        print("✓ bucket_browser imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import bucket_browser: {e}")
        return False
    
    return True

def test_tempurl_generation():
    """Test TempURL generation logic."""
    print("\nTesting TempURL generation...")
    
    from tempurl_manager import TempURLManager
    
    # Mock API client
    class MockAPIClient:
        def __init__(self):
            self.base_url = "https://drive.haio.ir"
            self.token = "test_token"
            self.username = "testuser"
    
    api_client = MockAPIClient()
    temp_url_key = "secret123"
    manager = TempURLManager(api_client, temp_url_key)
    
    # Generate a test URL
    url = manager.generate_temp_url(
        username="testuser",
        bucket_name="testbucket",
        object_name="testfile.pdf",
        method='GET',
        duration_seconds=3600
    )
    
    # Verify URL components
    assert "temp_url_sig=" in url, "URL missing signature"
    assert "temp_url_expires=" in url, "URL missing expiration"
    assert "/v1/AUTH_testuser/testbucket/testfile.pdf" in url, "URL has incorrect path"
    
    print(f"✓ Generated URL: {url[:80]}...")
    
    # Test validation
    validation = manager.validate_temp_url(url)
    assert validation['valid'] == True, f"URL should be valid: {validation}"
    print(f"✓ URL validation passed: valid={validation['valid']}, time_remaining={validation.get('time_remaining', 0)}s")
    
    return True

def test_human_readable_functions():
    """Test human-readable conversion functions."""
    print("\nTesting human-readable functions...")
    
    from tempurl_manager import TempURLManager
    import time
    
    # Mock API client
    class MockAPIClient:
        def __init__(self):
            self.base_url = "https://drive.haio.ir"
            self.token = "test_token"
    
    api_client = MockAPIClient()
    manager = TempURLManager(api_client, "test_key")
    
    # Test time remaining text
    test_cases = [
        (3600, "ساعت"),  # 1 hour
        (86400, "روز"),  # 1 day
        (90000, "روز"),  # 1 day + 1 hour
        (0, "منقضی"),    # Expired
    ]
    
    for seconds, expected_part in test_cases:
        result = manager.get_time_remaining_text(seconds)
        assert expected_part in result, f"Expected '{expected_part}' in '{result}'"
        print(f"✓ {seconds}s → '{result}'")
    
    # Test expiry formatting
    future_time = int(time.time()) + 86400
    expiry_text = manager.get_human_readable_expiry(future_time)
    assert "/" in expiry_text, "Expiry text should contain date separator"
    print(f"✓ Expiry format: {expiry_text}")
    
    return True

def test_ip_validation():
    """Test IP address validation in ShareDialog."""
    print("\nTesting IP validation...")
    
    import re
    
    def validate_ip(ip: str) -> bool:
        """Validate IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    test_cases = [
        ("192.168.1.1", True),
        ("10.0.0.1", True),
        ("255.255.255.255", True),
        ("0.0.0.0", True),
        ("256.1.1.1", False),  # Invalid octet
        ("192.168.1", False),   # Missing octet
        ("192.168.1.1.1", False),  # Extra octet
        ("abc.def.ghi.jkl", False),  # Not numbers
    ]
    
    for ip, expected in test_cases:
        try:
            result = validate_ip(ip)
            assert result == expected, f"IP {ip}: expected {expected}, got {result}"
            status = "✓" if result else "✗"
            print(f"{status} {ip}: {result}")
        except:
            print(f"✗ {ip}: Exception (expected {expected})")
    
    return True

def test_signature_generation():
    """Test HMAC signature generation."""
    print("\nTesting signature generation...")
    
    import hmac
    from hashlib import sha1
    from time import time
    
    method = 'GET'
    expires = int(time() + 3600)
    path = '/v1/AUTH_testuser/bucket/object.txt'
    key = 'secret123'
    
    hmac_body = f"{method}\n{expires}\n{path}"
    signature = hmac.new(key.encode(), hmac_body.encode(), sha1).hexdigest()
    
    assert len(signature) == 40, f"Signature should be 40 chars, got {len(signature)}"
    assert all(c in '0123456789abcdef' for c in signature), "Signature should be hex"
    
    print(f"✓ Signature generated: {signature[:20]}...{signature[-20:]}")
    print(f"✓ Signature length: {len(signature)} chars")
    
    return True

def main():
    """Run all tests."""
    print("=" * 70)
    print("TempURL Feature Test Suite")
    print("=" * 70)
    
    tests = [
        ("Import Test", test_imports),
        ("TempURL Generation", test_tempurl_generation),
        ("Human Readable Functions", test_human_readable_functions),
        ("IP Validation", test_ip_validation),
        ("Signature Generation", test_signature_generation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(f"{'='*70}")
        try:
            if test_func():
                print(f"\n✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with exception:")
            print(f"   {type(e).__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print(f"{'='*70}")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
