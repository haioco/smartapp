"""
TempURL Manager for Haio Smart Storage
Manages temporary URL generation and validation for secure file sharing
"""

import hmac
from hashlib import sha1
from time import time
from typing import Optional, Dict
import requests
from urllib.parse import urlparse, parse_qs


class TempURLManager:
    """Manages temporary URL generation and validation."""
    
    def __init__(self, api_client, temp_url_key: str):
        """
        Initialize TempURL Manager.
        
        Args:
            api_client: API client instance with authentication
            temp_url_key: Secret key for HMAC signature generation
        """
        self.api_client = api_client
        self.temp_url_key = temp_url_key
        self.base_url = api_client.base_url
    
    def set_temp_url_key(self, username: str, key: str) -> bool:
        """
        Set the X-Account-Meta-Temp-URL-Key header.
        
        Args:
            username: User account name
            key: Temporary URL key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            headers = {
                'X-Auth-Token': self.api_client.token,
                'X-Account-Meta-Temp-URL-Key': key
            }
            storage_url = f"{self.base_url}/v1/AUTH_{username}"
            resp = requests.post(storage_url, headers=headers, timeout=10)
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
        """
        Generate a temporary URL for an object.
        
        Args:
            username: User account name
            bucket_name: Container/bucket name
            object_name: Object name
            method: HTTP method (GET, PUT, POST, DELETE)
            duration_seconds: Validity duration in seconds
            ip_restriction: Optional IP address restriction
            
        Returns:
            Temporary URL string
        """
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
        """
        Generate a temporary URL for all objects with a prefix.
        
        Args:
            username: User account name
            bucket_name: Container/bucket name
            prefix: Object prefix
            method: HTTP method (GET, PUT, POST, DELETE)
            duration_seconds: Validity duration in seconds
            
        Returns:
            Temporary URL string for prefix-based access
        """
        expires = int(time() + duration_seconds)
        path = f"/v1/AUTH_{username}/{bucket_name}/{prefix}"
        
        hmac_body = f"prefix:{method}\n{expires}\n{path}"
        signature = hmac.new(
            self.temp_url_key.encode(),
            hmac_body.encode(),
            sha1
        ).hexdigest()
        
        return f"{self.base_url}{path}?temp_url_sig={signature}&temp_url_expires={expires}"
    
    def validate_temp_url(self, url: str) -> Dict:
        """
        Validate and parse a temporary URL.
        
        Args:
            url: Temporary URL to validate
            
        Returns:
            Dictionary with validation results:
            - valid: Boolean indicating if URL is valid
            - expires_at: Expiration timestamp (if valid)
            - time_remaining: Seconds until expiration (if valid)
            - reason: Error reason (if invalid)
        """
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            sig = query_params.get('temp_url_sig', [None])[0]
            expires = query_params.get('temp_url_expires', [None])[0]
            
            if not sig or not expires:
                return {'valid': False, 'reason': 'مشخصات امضا یا تاریخ انقضا موجود نیست'}
            
            try:
                expires_int = int(expires)
                current_time = int(time())
                
                if current_time > expires_int:
                    return {
                        'valid': False,
                        'reason': 'لینک منقضی شده است',
                        'expired_at': expires_int
                    }
                
                return {
                    'valid': True,
                    'expires_at': expires_int,
                    'time_remaining': expires_int - current_time
                }
            except ValueError:
                return {'valid': False, 'reason': 'فرمت تاریخ انقضا نامعتبر است'}
                
        except Exception as e:
            return {'valid': False, 'reason': f'خطا در بررسی لینک: {str(e)}'}
    
    def get_human_readable_expiry(self, expires_timestamp: int) -> str:
        """
        Convert expiration timestamp to human-readable format.
        
        Args:
            expires_timestamp: Unix timestamp
            
        Returns:
            Human-readable date and time string
        """
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(expires_timestamp)
            return dt.strftime('%Y/%m/%d - %H:%M')
        except:
            return "نامعلوم"
    
    def get_time_remaining_text(self, seconds: int) -> str:
        """
        Convert seconds to human-readable time remaining text.
        
        Args:
            seconds: Seconds remaining
            
        Returns:
            Formatted string like "2 روز و 3 ساعت"
        """
        if seconds <= 0:
            return "منقضی شده"
        
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} روز")
        if hours > 0:
            parts.append(f"{hours} ساعت")
        if minutes > 0 and days == 0:  # Only show minutes if less than a day
            parts.append(f"{minutes} دقیقه")
        
        return " و ".join(parts) if parts else "کمتر از یک دقیقه"
