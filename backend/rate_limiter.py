# Rate Limiting Configuration
"""
Simple in-memory rate limiter using sliding window algorithm.
For production, use Redis-based rate limiting with slowapi or similar.
"""

import time
from collections import defaultdict, deque
from typing import Dict, Tuple
from fastapi import HTTPException, Request
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter with sliding window algorithm.
    
    For production, replace with Redis-based limiter:
    - pip install slowapi
    - from slowapi import Limiter, _rate_limit_exceeded_handler
    """
    
    def __init__(self):
        # Format: {endpoint: {client_ip: deque([timestamp1, timestamp2, ...])}}
        self.requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
    
    def is_rate_limited(
        self,
        client_ip: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Check if request should be rate limited.
        
        Args:
            client_ip: Client IP address
            endpoint: API endpoint path
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            (is_limited, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Get request history for this client/endpoint
        history = self.requests[endpoint][client_ip]
        
        # Remove old requests outside the window
        while history and history[0] < window_start:
            history.popleft()
        
        # Check if limit exceeded
        if len(history) >= max_requests:
            # Calculate retry-after (time until oldest request expires)
            oldest_request = history[0]
            retry_after = int(oldest_request + window_seconds - now) + 1
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {endpoint}: "
                f"{len(history)}/{max_requests} requests in {window_seconds}s"
            )
            return True, retry_after
        
        # Add current request
        history.append(now)
        return False, 0
    
    def cleanup_old_entries(self):
        """Remove old entries to prevent memory bloat (run periodically)."""
        now = time.time()
        for endpoint in list(self.requests.keys()):
            for client_ip in list(self.requests[endpoint].keys()):
                history = self.requests[endpoint][client_ip]
                # Keep last 1 hour of data max
                while history and history[0] < now - 3600:
                    history.popleft()
                # Remove empty histories
                if not history:
                    del self.requests[endpoint][client_ip]
            # Remove empty endpoints
            if not self.requests[endpoint]:
                del self.requests[endpoint]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    Rate limit decorator for FastAPI endpoints.
    
    Usage:
        @app.post("/login")
        @rate_limit(max_requests=5, window_seconds=60)  # 5 requests per minute
        async def login(request: Request, ...):
            ...
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Get client IP
            client_ip = request.client.host if request.client else "unknown"
            
            # Check X-Forwarded-For header (if behind proxy)
            if "X-Forwarded-For" in request.headers:
                client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
            
            # Get endpoint path
            endpoint = request.url.path
            
            # Check rate limit
            is_limited, retry_after = rate_limiter.is_rate_limited(
                client_ip, endpoint, max_requests, window_seconds
            )
            
            if is_limited:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
            
            # Execute endpoint
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# Cleanup task (run every 10 minutes)
async def cleanup_rate_limiter():
    """Background task to cleanup old rate limit entries."""
    while True:
        await asyncio.sleep(600)  # 10 minutes
        rate_limiter.cleanup_old_entries()
        logger.info("Rate limiter cleanup completed")


import asyncio
