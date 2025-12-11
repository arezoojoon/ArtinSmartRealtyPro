"""
Multi-Vertical Routing System
Routes WhatsApp users to different business verticals (Real Estate, Expo, etc.)
Uses Redis for session persistence and deep link detection for entry points.
"""

import logging
import re
from typing import Optional, Dict, Any, List
from enum import Enum
from database import Tenant, Lead
from redis_manager import RedisManager

logger = logging.getLogger(__name__)


class VerticalMode(str, Enum):
    """Available business verticals"""
    REALTY = "realty"
    EXPO = "expo"
    SUPPORT = "support"
    NONE = "none"


class VerticalRouter:
    """
    Routes users to appropriate business vertical based on:
    1. Deep link keywords (start_expo, start_realty)
    2. Existing Redis session
    3. Main menu selection
    """
    
    # Deep link keywords for each vertical
    # These are used in WhatsApp deep links like: wa.me/971505037158?text=start_realty
    DEEP_LINK_PATTERNS = {
        VerticalMode.REALTY: [
            r'\bstart[_\s-]?realty\b',
            r'\brealestate\b',
            r'\bproperty\b',
            r'\bamlak\b',  # Persian for real estate
            r'\بstart[_\s-]?املاک\b',  # Persian deep link
        ],
        VerticalMode.EXPO: [
            r'\bstart[_\s-]?expo\b',
            r'\bevent\b',
            r'\bexhibition\b',
            r'\bstart[_\s-]?travel\b',  # Travel/tourism vertical
            r'\bstart[_\s-]?clinic\b',  # Medical tourism
            r'\بstart[_\s-]?نمایشگاه\b',  # Persian for expo
        ],
        VerticalMode.SUPPORT: [
            r'\bsupport\b',
            r'\bhelp\b',
            r'\bassistance\b',
            r'\بپشتیبانی\b',  # Persian for support
        ]
    }
    
    # Session expiry (24 hours in seconds)
    SESSION_TTL = 86400
    
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager
    
    async def get_user_mode(self, user_phone: str) -> VerticalMode:
        """
        Get current vertical mode for user from Redis session.
        Returns VerticalMode.NONE if no session exists.
        """
        if not self.redis.redis_client:
            logger.warning("Redis not available, returning NONE mode")
            return VerticalMode.NONE
        
        try:
            mode_key = f"user:{user_phone}:mode"
            mode_value = await self.redis.redis_client.get(mode_key)
            
            if mode_value:
                mode_str = mode_value.decode('utf-8') if isinstance(mode_value, bytes) else mode_value
                try:
                    return VerticalMode(mode_str)
                except ValueError:
                    logger.warning(f"Invalid mode value: {mode_str}, resetting to NONE")
                    await self.redis.redis_client.delete(mode_key)
            
            return VerticalMode.NONE
        except Exception as e:
            logger.error(f"Error getting user mode: {e}")
            return VerticalMode.NONE
    
    async def set_user_mode(self, user_phone: str, mode: VerticalMode) -> bool:
        """
        Set vertical mode for user in Redis with TTL.
        Returns True if successful.
        """
        if not self.redis.redis_client:
            logger.warning("Redis not available, cannot set mode")
            return False
        
        try:
            mode_key = f"user:{user_phone}:mode"
            await self.redis.redis_client.set(
                mode_key, 
                mode.value, 
                ex=self.SESSION_TTL
            )
            logger.info(f"Set user {user_phone} to mode: {mode.value}")
            return True
        except Exception as e:
            logger.error(f"Error setting user mode: {e}")
            return False
    
    async def clear_user_mode(self, user_phone: str) -> bool:
        """Clear user's vertical mode (logout/reset)."""
        if not self.redis.redis_client:
            return False
        
        try:
            mode_key = f"user:{user_phone}:mode"
            await self.redis.redis_client.delete(mode_key)
            logger.info(f"Cleared mode for user {user_phone}")
            return True
        except Exception as e:
            logger.error(f"Error clearing user mode: {e}")
            return False
    
    def detect_deep_link(self, message_text: str) -> Optional[VerticalMode]:
        """
        Detect deep link keyword in message.
        Returns VerticalMode if detected, None otherwise.
        """
        if not message_text:
            return None
        
        message_lower = message_text.lower().strip()
        
        # Check each vertical's patterns
        for mode, patterns in self.DEEP_LINK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    logger.info(f"Deep link detected: {mode.value} (pattern: {pattern})")
                    return mode
        
        return None
    
    def is_menu_selection(self, message_text: str) -> Optional[VerticalMode]:
        """
        Check if message is a menu selection (interactive button/list response).
        Returns VerticalMode if valid selection, None otherwise.
        """
        if not message_text:
            return None
        
        message_lower = message_text.lower().strip()
        
        # Menu option keywords
        if any(kw in message_lower for kw in ['realty', 'real estate', 'property', 'ملک', 'املاک']):
            return VerticalMode.REALTY
        elif any(kw in message_lower for kw in ['expo', 'event', 'exhibition', 'نمایشگاه', 'رویداد']):
            return VerticalMode.EXPO
        elif any(kw in message_lower for kw in ['support', 'help', 'پشتیبانی', 'کمک']):
            return VerticalMode.SUPPORT
        
        return None
    
    async def route_message(
        self, 
        user_phone: str, 
        message_text: str
    ) -> tuple[VerticalMode, bool]:
        """
        Main routing logic. Returns (VerticalMode, is_new_session).
        
        Priority:
        1. Deep link detection (overrides existing session)
        2. Existing Redis session
        3. Menu selection
        4. None (triggers main menu)
        """
        # 1. Check for deep link (highest priority)
        deep_link_mode = self.detect_deep_link(message_text)
        if deep_link_mode and deep_link_mode != VerticalMode.NONE:
            await self.set_user_mode(user_phone, deep_link_mode)
            return (deep_link_mode, True)  # New session
        
        # 2. Check existing session
        current_mode = await self.get_user_mode(user_phone)
        if current_mode != VerticalMode.NONE:
            # Extend TTL on each interaction
            await self.set_user_mode(user_phone, current_mode)
            return (current_mode, False)  # Existing session
        
        # 3. Check if message is menu selection
        menu_mode = self.is_menu_selection(message_text)
        if menu_mode and menu_mode != VerticalMode.NONE:
            await self.set_user_mode(user_phone, menu_mode)
            return (menu_mode, True)  # New session from menu
        
        # 4. No mode detected - trigger main menu
        return (VerticalMode.NONE, False)
    
    def get_main_menu_content(self, tenant: Tenant, language: str = "EN") -> Dict[str, Any]:
        """
        Generate main menu content for WhatsApp interactive list.
        Returns dict with menu structure.
        """
        agent_name = tenant.name or "Artin SmartAgent"
        
        # Multi-language support
        messages = {
            "EN": {
                "header": f"Welcome to {agent_name}",
                "body": "Please select a service to get started:",
                "button": "📋 Select Service",
                "sections": [
                    {
                        "title": "Available Services",
                        "rows": [
                            {
                                "id": "start_realty",
                                "title": "🏠 Real Estate",
                                "description": "Property search & investment"
                            },
                            {
                                "id": "start_expo",
                                "title": "🎪 Events & Expo",
                                "description": "Exhibition assistance"
                            },
                            {
                                "id": "support",
                                "title": "📞 Support",
                                "description": "Get help from our team"
                            }
                        ]
                    }
                ]
            },
            "FA": {
                "header": f"به {agent_name} خوش آمدید",
                "body": "لطفاً یک سرویس را انتخاب کنید:",
                "button": "📋 انتخاب سرویس",
                "sections": [
                    {
                        "title": "سرویس‌های موجود",
                        "rows": [
                            {
                                "id": "start_realty",
                                "title": "🏠 املاک و مستغلات",
                                "description": "جستجو و سرمایه‌گذاری ملکی"
                            },
                            {
                                "id": "start_expo",
                                "title": "🎪 نمایشگاه و رویداد",
                                "description": "راهنمای نمایشگاه"
                            },
                            {
                                "id": "support",
                                "title": "📞 پشتیبانی",
                                "description": "دریافت کمک از تیم ما"
                            }
                        ]
                    }
                ]
            },
            "AR": {
                "header": f"مرحباً بك في {agent_name}",
                "body": "الرجاء اختيار خدمة للبدء:",
                "button": "📋 اختر الخدمة",
                "sections": [
                    {
                        "title": "الخدمات المتاحة",
                        "rows": [
                            {
                                "id": "start_realty",
                                "title": "🏠 العقارات",
                                "description": "البحث عن العقارات والاستثمار"
                            },
                            {
                                "id": "start_expo",
                                "title": "🎪 المعارض والفعاليات",
                                "description": "مساعدة المعرض"
                            },
                            {
                                "id": "support",
                                "title": "📞 الدعم",
                                "description": "احصل على المساعدة من فريقنا"
                            }
                        ]
                    }
                ]
            }
        }
        
        return messages.get(language.upper(), messages["EN"])


# Singleton instance
_router_instance: Optional[VerticalRouter] = None


def get_vertical_router(redis_manager: RedisManager) -> VerticalRouter:
    """Get or create VerticalRouter singleton."""
    global _router_instance
    if _router_instance is None:
        _router_instance = VerticalRouter(redis_manager)
    return _router_instance
