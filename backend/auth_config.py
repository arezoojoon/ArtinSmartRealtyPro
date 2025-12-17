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


# ==================== AUTHENTICATION FUNCTIONS ====================

import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 600,000 iterations."""
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        PASSWORD_SALT.encode(),
        600000
    ).hex()


def decode_jwt_token(token: str) -> dict:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def verify_super_admin(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify that the request is from super admin (tenant_id = 0)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = credentials.credentials
        payload = decode_jwt_token(token)
        tenant_id = payload.get("tenant_id")
        
        if tenant_id != 0:  # Super admin has tenant_id = 0
            raise HTTPException(status_code=403, detail="Super admin access required")
        
        return payload
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


async def verify_tenant_access(
    credentials: HTTPAuthorizationCredentials,
    tenant_id: int,
    db: AsyncSession
):
    """
    Verify that the authenticated user has access to the given tenant.
    Super Admin (tenant_id=0) can access any tenant.
    Regular tenants can only access their own data.
    """
    from database import Tenant  # Import here to avoid circular dependency
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_jwt_token(credentials.credentials)
    auth_tenant_id = payload.get("tenant_id")
    
    # Super Admin can access any tenant
    if auth_tenant_id == 0:
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tenant
    
    # Regular tenant can only access their own data
    if auth_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant
