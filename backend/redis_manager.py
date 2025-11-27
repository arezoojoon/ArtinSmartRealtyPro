"""
Redis Manager for Bot Context Persistence
Stores user conversation state for session recovery
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Session TTL (Time To Live)
SESSION_TTL_HOURS = 24  # User context expires after 24 hours


class RedisManager:
    """Manages Redis connections and bot context storage."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection."""
        try:
            self.redis_client = await redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            await self.redis_client.ping()
            logger.info(f"✅ Redis connected: {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def _get_session_key(self, telegram_id: int, tenant_id: int) -> str:
        """Generate Redis key for user session."""
        return f"bot:session:{tenant_id}:{telegram_id}"
    
    def _get_timeout_key(self, telegram_id: int, tenant_id: int) -> str:
        """Generate Redis key for timeout tracking."""
        return f"bot:timeout:{tenant_id}:{telegram_id}"
    
    async def save_context(
        self,
        telegram_id: int,
        tenant_id: int,
        context: Dict[str, Any]
    ) -> bool:
        """
        Save user conversation context to Redis.
        
        Args:
            telegram_id: Telegram user ID
            tenant_id: Tenant ID
            context: Dictionary with conversation state, filled_slots, pending_slot, etc.
        
        Returns:
            True if saved successfully
        """
        if not self.redis_client:
            logger.warning("Redis not available, skipping context save")
            return False
        
        try:
            key = self._get_session_key(telegram_id, tenant_id)
            context_json = json.dumps(context, ensure_ascii=False)
            
            await self.redis_client.setex(
                key,
                timedelta(hours=SESSION_TTL_HOURS),
                context_json
            )
            logger.info(f"💾 Context saved for user {telegram_id} (tenant {tenant_id})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save context: {e}")
            return False
    
    async def get_context(
        self,
        telegram_id: int,
        tenant_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve user conversation context from Redis.
        
        EDGE CASE PROTECTION: If key expired at exactly 24h, return None gracefully.
        Bot will detect missing context and create new session.
        """
        if not self.redis_client:
            return None
        
        try:
            key = self._get_session_key(telegram_id, tenant_id)
            context_json = await self.redis_client.get(key)
            
            if context_json:
                context = json.loads(context_json)
                logger.info(f"📥 Context retrieved for user {telegram_id}")
                return context
            else:
                # TTL EXPIRED - not an error, just log it
                logger.info(f"⏱️ Session expired for user {telegram_id} - will create new session")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"⚠️ Corrupted context data for user {telegram_id}: {e}")
            # Delete corrupted key
            await self.delete_context(telegram_id, tenant_id)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get context: {e}")
            return None
    
    async def delete_context(
        self,
        telegram_id: int,
        tenant_id: int
    ) -> bool:
        """Delete user session context."""
        if not self.redis_client:
            return False
        
        try:
            key = self._get_session_key(telegram_id, tenant_id)
            await self.redis_client.delete(key)
            logger.info(f"🗑️ Context deleted for user {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete context: {e}")
            return False
    
    async def set_timeout_tracker(
        self,
        telegram_id: int,
        tenant_id: int,
        state: str,
        timeout_minutes: int = 10
    ) -> bool:
        """
        Set timeout tracker for follow-up message.
        
        Args:
            telegram_id: Telegram user ID
            tenant_id: Tenant ID
            state: Current conversation state
            timeout_minutes: Minutes to wait before sending follow-up
        
        Returns:
            True if set successfully
        """
        if not self.redis_client:
            return False
        
        try:
            key = self._get_timeout_key(telegram_id, tenant_id)
            timeout_data = {
                "state": state,
                "timestamp": json.dumps(None),  # Will be set by scheduler
                "sent": False
            }
            
            await self.redis_client.setex(
                key,
                timedelta(minutes=timeout_minutes),
                json.dumps(timeout_data)
            )
            logger.info(f"⏱️ Timeout tracker set for user {telegram_id} ({timeout_minutes}m)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set timeout tracker: {e}")
            return False
    
    async def get_timeout_tracker(
        self,
        telegram_id: int,
        tenant_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get timeout tracker data."""
        if not self.redis_client:
            return None
        
        try:
            key = self._get_timeout_key(telegram_id, tenant_id)
            data = await self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"❌ Failed to get timeout tracker: {e}")
            return None
    
    async def clear_timeout_tracker(
        self,
        telegram_id: int,
        tenant_id: int
    ) -> bool:
        """Clear timeout tracker (user responded)."""
        if not self.redis_client:
            return False
        
        try:
            key = self._get_timeout_key(telegram_id, tenant_id)
            await self.redis_client.delete(key)
            logger.info(f"✅ Timeout tracker cleared for user {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear timeout tracker: {e}")
            return False
    
    async def mark_timeout_sent(
        self,
        telegram_id: int,
        tenant_id: int
    ) -> bool:
        """Mark that follow-up message was sent."""
        if not self.redis_client:
            return False
        
        try:
            key = self._get_timeout_key(telegram_id, tenant_id)
            data = await self.get_timeout_tracker(telegram_id, tenant_id)
            
            if data:
                data["sent"] = True
                await self.redis_client.setex(
                    key,
                    timedelta(minutes=5),  # Keep for 5 more minutes
                    json.dumps(data)
                )
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to mark timeout sent: {e}")
            return False


# Global instance
redis_manager = RedisManager()


async def init_redis():
    """Initialize Redis connection on startup."""
    await redis_manager.connect()


async def close_redis():
    """Close Redis connection on shutdown."""
    await redis_manager.disconnect()
