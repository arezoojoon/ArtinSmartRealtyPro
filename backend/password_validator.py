"""
Password Strength Validator
Enforces strong password policies to prevent weak passwords
"""

import re
from typing import Tuple, List
from fastapi import HTTPException


class PasswordValidator:
    """
    Validate password strength according to OWASP guidelines.
    
    Requirements:
    - Minimum 8 characters (12+ recommended)
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    - No common passwords
    - No sequential characters
    """
    
    # Common weak passwords (top 100)
    COMMON_PASSWORDS = {
        "password", "12345678", "123456789", "12345", "1234567", "password1",
        "123456", "qwerty", "abc123", "111111", "1234567890", "admin",
        "letmein", "welcome", "monkey", "dragon", "master", "sunshine",
        "princess", "login", "admin123", "welcome123", "pass123", "password123",
        "iloveyou", "football", "baseball", "starwars", "superman", "batman",
        "trustno1", "freedom", "whatever", "qazwsx", "mustang", "michael",
        "shadow", "ashley", "bailey", "passw0rd", "admin@123", "root",
        "toor", "test", "guest", "oracle", "default", "changeme", "P@ssw0rd",
        "P@ssword", "Password1", "Qwerty123", "Welcome1", "Admin123"
    }
    
    @staticmethod
    def validate(password: str, min_length: int = 8) -> Tuple[bool, List[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            min_length: Minimum required length (default 8)
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check minimum length
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long")
        
        # Check maximum length (prevent DoS via extremely long passwords)
        if len(password) > 128:
            errors.append("Password must not exceed 128 characters")
        
        # Check for uppercase
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for digits
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            errors.append("Password must contain at least one special character (!@#$%^&*...)")
        
        # Check against common passwords
        if password.lower() in PasswordValidator.COMMON_PASSWORDS:
            errors.append("Password is too common and easily guessable")
        
        # Check for sequential characters (123, abc, etc.)
        if PasswordValidator._has_sequential_chars(password):
            errors.append("Password contains sequential characters (e.g., 123, abc)")
        
        # Check for repeated characters (aaa, 111, etc.)
        if PasswordValidator._has_repeated_chars(password):
            errors.append("Password contains too many repeated characters")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _has_sequential_chars(password: str, min_seq: int = 3) -> bool:
        """Check if password contains sequential characters."""
        password_lower = password.lower()
        
        # Check numeric sequences (123, 234, etc.)
        for i in range(len(password_lower) - min_seq + 1):
            substring = password_lower[i:i + min_seq]
            if substring.isdigit():
                digits = [int(c) for c in substring]
                if all(digits[j] + 1 == digits[j + 1] for j in range(len(digits) - 1)):
                    return True
                if all(digits[j] - 1 == digits[j + 1] for j in range(len(digits) - 1)):
                    return True
        
        # Check alphabetic sequences (abc, xyz, etc.)
        for i in range(len(password_lower) - min_seq + 1):
            substring = password_lower[i:i + min_seq]
            if substring.isalpha():
                chars = [ord(c) for c in substring]
                if all(chars[j] + 1 == chars[j + 1] for j in range(len(chars) - 1)):
                    return True
                if all(chars[j] - 1 == chars[j + 1] for j in range(len(chars) - 1)):
                    return True
        
        return False
    
    @staticmethod
    def _has_repeated_chars(password: str, max_repeat: int = 3) -> bool:
        """Check if password has too many repeated characters."""
        for i in range(len(password) - max_repeat + 1):
            if len(set(password[i:i + max_repeat])) == 1:
                return True
        return False
    
    @staticmethod
    def validate_or_raise(password: str, min_length: int = 8) -> None:
        """
        Validate password and raise HTTPException if invalid.
        
        Usage in FastAPI:
            from password_validator import PasswordValidator
            
            @app.post("/register")
            async def register(password: str):
                PasswordValidator.validate_or_raise(password)
                # Password is strong, proceed...
        """
        is_valid, errors = PasswordValidator.validate(password, min_length)
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Password does not meet security requirements",
                    "requirements": errors
                }
            )


# Convenience function
def validate_password_strength(password: str, min_length: int = 8) -> None:
    """Validate password strength (raises HTTPException if invalid)."""
    PasswordValidator.validate_or_raise(password, min_length)
