"""
Input Sanitization and Validation
Prevents injection attacks and malicious input
"""

import re
import html
from typing import Optional, Any
from fastapi import HTTPException


class InputSanitizer:
    """
    Sanitize user input to prevent injection attacks.
    
    Protections:
    - XSS (Cross-Site Scripting)
    - SQL Injection patterns
    - Command Injection
    - Path Traversal
    - LDAP Injection
    - XML Injection
    """
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"('|(\\')|(;\s*--)|(\bOR\b.*=.*)|(\bAND\b.*=.*)",
        r"(\bUNION\b.*\bSELECT\b)|(\bINSERT\b.*\bINTO\b)|(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)|(\bDROP\b.*\bTABLE\b)|(\bEXEC\b)|(\bEXECUTE\b)",
        r"(xp_cmdshell)|(sp_executesql)",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",  # Shell metacharacters
        r"(\.\./)|(\.\\.)",  # Path traversal
        r"(<script.*?>.*?</script>)",  # Script tags
        r"(eval\s*\()",  # eval() calls
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers (onclick, onerror, etc.)
        r"<iframe",
        r"<object",
        r"<embed",
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None, allow_html: bool = False) -> str:
        """
        Sanitize string input.
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            allow_html: If True, allows safe HTML tags
        
        Returns:
            Sanitized string
        
        Raises:
            HTTPException: If input contains malicious patterns
        """
        if not isinstance(value, str):
            raise HTTPException(status_code=400, detail="Input must be a string")
        
        # Check length
        if max_length and len(value) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Input exceeds maximum length of {max_length} characters"
            )
        
        # Check for SQL injection patterns
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Input contains suspicious SQL patterns"
                )
        
        # Check for command injection patterns
        for pattern in InputSanitizer.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Input contains suspicious command patterns"
                )
        
        # Check for XSS patterns
        if not allow_html:
            for pattern in InputSanitizer.XSS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    raise HTTPException(
                        status_code=400,
                        detail="Input contains suspicious XSS patterns"
                    )
            
            # HTML escape for safety
            value = html.escape(value)
        
        # Remove null bytes (can cause issues in C-based libraries)
        value = value.replace('\x00', '')
        
        # Strip leading/trailing whitespace
        value = value.strip()
        
        return value
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitize email address.
        
        Args:
            email: Email address
        
        Returns:
            Sanitized email (lowercase)
        
        Raises:
            HTTPException: If email is invalid
        """
        email = email.strip().lower()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check length
        if len(email) > 255:
            raise HTTPException(status_code=400, detail="Email too long")
        
        # Check for suspicious patterns
        suspicious = ['script', 'javascript:', '<', '>', ';', '--']
        if any(s in email.lower() for s in suspicious):
            raise HTTPException(status_code=400, detail="Email contains invalid characters")
        
        return email
    
    @staticmethod
    def sanitize_phone(phone: str) -> str:
        """
        Sanitize phone number.
        
        Args:
            phone: Phone number
        
        Returns:
            Sanitized phone (digits, +, -, spaces only)
        """
        # Remove all characters except digits, +, -, spaces, parentheses
        phone = re.sub(r'[^0-9+\-\s()]', '', phone)
        
        # Strip whitespace
        phone = phone.strip()
        
        # Validate length (international format: 7-15 digits)
        digits_only = re.sub(r'[^0-9]', '', phone)
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise HTTPException(status_code=400, detail="Invalid phone number length")
        
        return phone
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitize URL.
        
        Args:
            url: URL string
        
        Returns:
            Sanitized URL
        
        Raises:
            HTTPException: If URL is invalid or contains malicious patterns
        """
        url = url.strip()
        
        # Check for javascript: and data: URLs (XSS vectors)
        if url.lower().startswith(('javascript:', 'data:', 'vbscript:')):
            raise HTTPException(status_code=400, detail="Invalid URL scheme")
        
        # Only allow http:// and https://
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        
        # Check length
        if len(url) > 2048:
            raise HTTPException(status_code=400, detail="URL too long")
        
        return url
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        Args:
            filename: Original filename
        
        Returns:
            Safe filename
        """
        # Remove path separators and parent directory references
        filename = filename.replace('/', '').replace('\\', '').replace('..', '')
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Only allow alphanumeric, dots, dashes, underscores
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:240] + ('.' + ext if ext else '')
        
        # Prevent empty filename
        if not filename or filename == '.':
            filename = 'file'
        
        return filename
    
    @staticmethod
    def sanitize_json_field(value: Any, field_name: str, max_length: Optional[int] = None) -> Any:
        """
        Sanitize JSON field value.
        
        Args:
            value: Field value (can be str, int, float, bool, None)
            field_name: Name of the field (for error messages)
            max_length: Maximum string length
        
        Returns:
            Sanitized value
        """
        if value is None:
            return None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            # Check for unreasonably large numbers (potential DoS)
            if abs(value) > 1e15:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' has unreasonably large value"
                )
            return value
        
        if isinstance(value, str):
            return InputSanitizer.sanitize_string(value, max_length)
        
        if isinstance(value, (list, dict)):
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field_name}' has invalid type (nested objects not allowed here)"
            )
        
        return value


# Convenience functions
def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize general text input."""
    return InputSanitizer.sanitize_string(text, max_length=max_length, allow_html=False)


def sanitize_email(email: str) -> str:
    """Sanitize email address."""
    return InputSanitizer.sanitize_email(email)


def sanitize_phone(phone: str) -> str:
    """Sanitize phone number."""
    return InputSanitizer.sanitize_phone(phone)
