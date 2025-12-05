"""
Shared JWT Authentication Configuration
This module ensures JWT_SECRET is initialized once and shared across all modules.
"""

import os
import secrets

# Initialize JWT_SECRET once - either from environment or generate and cache
_JWT_SECRET = None

def get_jwt_secret() -> str:
    """Get or initialize JWT secret (singleton pattern)."""
    global _JWT_SECRET
    if _JWT_SECRET is None:
        _JWT_SECRET = os.getenv("JWT_SECRET")
        if not _JWT_SECRET:
            # Generate a secret and warn in production
            _JWT_SECRET = secrets.token_hex(32)
            import logging
            logging.warning(
                "JWT_SECRET not found in environment variables! "
                "Generated temporary secret. This will change on restart. "
                "Set JWT_SECRET in .env for production!"
            )
    return _JWT_SECRET

# Constants
JWT_SECRET = get_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
PASSWORD_SALT = os.getenv("PASSWORD_SALT", "artinsmartrealty_salt_v2")
