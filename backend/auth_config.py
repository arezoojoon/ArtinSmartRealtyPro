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
            # Security: REQUIRE JWT_SECRET - never auto-generate
            import logging
            
            # Check if development mode
            environment = os.getenv("ENVIRONMENT", "development")
            
            if environment == "production":
                # Production: FAIL HARD
                raise RuntimeError(
                    "SECURITY ERROR: JWT_SECRET not set in environment!\n"
                    "Generate one: openssl rand -hex 32\n"
                    "Add to .env: JWT_SECRET=<generated_secret>"
                )
            else:
                # Development: Generate but warn loudly
                _JWT_SECRET = secrets.token_hex(32)
                logging.warning(
                    "⚠️  JWT_SECRET not found! Generated temporary secret for DEVELOPMENT.\n"
                    "⚠️  All sessions will be invalidated on restart.\n"
                    "⚠️  For production, set JWT_SECRET in .env!"
                )
    return _JWT_SECRET

# Constants
JWT_SECRET = get_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security: Require password salt in environment
PASSWORD_SALT = os.getenv("PASSWORD_SALT")
if not PASSWORD_SALT:
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        raise RuntimeError(
            "SECURITY ERROR: PASSWORD_SALT not set in environment!\n"
            "Generate one: openssl rand -hex 16\n"
            "Add to .env: PASSWORD_SALT=<generated_salt>"
        )
    else:
        # Development: Use default but warn
        PASSWORD_SALT = "artinsmartrealty_dev_salt_INSECURE"
        import logging
        logging.warning(
            "⚠️  PASSWORD_SALT not found! Using insecure default for DEVELOPMENT.\n"
            "⚠️  For production, set PASSWORD_SALT in .env!"
        )
