"""
Centralized Error Handling & Logging
Provides user-friendly error messages and structured logging
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log')
    ]
)

logger = logging.getLogger(__name__)


class UserFriendlyError(HTTPException):
    """Base class for user-friendly errors"""
    def __init__(self, status_code: int, message: str, details: Optional[Dict[str, Any]] = None):
        self.user_message = message
        self.technical_details = details or {}
        super().__init__(status_code=status_code, detail=message)


class DatabaseError(UserFriendlyError):
    """Database operation failed"""
    def __init__(self, operation: str, details: Optional[str] = None):
        message = f"عملیات دیتابیس ({operation}) با خطا مواجه شد. لطفاً دوباره تلاش کنید."
        super().__init__(
            status_code=500,
            message=message,
            details={"operation": operation, "error": details}
        )


class ValidationError(UserFriendlyError):
    """Input validation failed"""
    def __init__(self, field: str, reason: str):
        message = f"❌ خطا در فیلد '{field}': {reason}"
        super().__init__(
            status_code=400,
            message=message,
            details={"field": field, "reason": reason}
        )


class ResourceNotFoundError(UserFriendlyError):
    """Resource not found"""
    def __init__(self, resource: str, identifier: Any):
        message = f"❌ {resource} با شناسه '{identifier}' پیدا نشد."
        super().__init__(
            status_code=404,
            message=message,
            details={"resource": resource, "id": identifier}
        )


class RateLimitError(UserFriendlyError):
    """Rate limit exceeded"""
    def __init__(self, service: str, retry_after: int = 60):
        message = f"⏳ محدودیت استفاده از {service}. لطفاً {retry_after} ثانیه صبر کنید."
        super().__init__(
            status_code=429,
            message=message,
            details={"service": service, "retry_after": retry_after}
        )


class ExternalServiceError(UserFriendlyError):
    """External API call failed"""
    def __init__(self, service: str, details: Optional[str] = None):
        message = f"⚠️ سرویس {service} موقتاً در دسترس نیست. لطفاً بعداً تلاش کنید."
        super().__init__(
            status_code=503,
            message=message,
            details={"service": service, "error": details}
        )


def handle_exception(e: Exception, context: str) -> HTTPException:
    """
    Convert any exception to user-friendly HTTPException
    
    Args:
        e: The exception
        context: Description of what was being done
        
    Returns:
        HTTPException with friendly message
    """
    
    # Log the full error for debugging
    logger.error(f"❌ Error in {context}: {type(e).__name__}: {str(e)}", exc_info=True)
    
    # Database errors
    if isinstance(e, IntegrityError):
        if "UNIQUE constraint" in str(e) or "duplicate" in str(e).lower():
            return ValidationError("داده", "این مقدار قبلاً استفاده شده است")
        return DatabaseError("ذخیره‌سازی", "تکراری بودن داده")
    
    elif isinstance(e, SQLAlchemyError):
        return DatabaseError(context, str(e))
    
    # Validation errors
    elif isinstance(e, ValidationError):
        return HTTPException(
            status_code=400,
            detail=f"❌ خطا در اعتبارسنجی داده: {str(e)}"
        )
    
    # Already user-friendly errors
    elif isinstance(e, UserFriendlyError):
        return e
    
    # Gemini API errors
    elif "google.generativeai" in str(type(e)):
        error_msg = str(e).lower()
        if "api_key" in error_msg or "invalid" in error_msg:
            return ExternalServiceError(
                "Gemini AI",
                "کلید API نامعتبر است. لطفاً تنظیمات را بررسی کنید."
            )
        elif "quota" in error_msg or "rate" in error_msg:
            return RateLimitError("Gemini AI", 60)
        else:
            return ExternalServiceError("Gemini AI", str(e))
    
    # Telegram/WhatsApp errors
    elif "telegram" in context.lower() or "whatsapp" in context.lower():
        return ExternalServiceError(
            "Telegram" if "telegram" in context.lower() else "WhatsApp",
            "ارسال پیام موفق نبود. لطفاً اتصال را بررسی کنید."
        )
    
    # Generic fallback
    else:
        logger.error(f"Unhandled exception type: {type(e).__name__}")
        return HTTPException(
            status_code=500,
            detail=f"❌ خطای سیستمی رخ داد. لطفاً با پشتیبانی تماس بگیرید. کد خطا: {context}"
        )


def log_business_event(event_type: str, data: Dict[str, Any]):
    """
    Log important business events
    
    Examples:
        - Lead created
        - Message sent
        - Property matched
        - Follow-up scheduled
    """
    logger.info(f"📊 BUSINESS_EVENT | {event_type} | {data}")


def log_performance(operation: str, duration_ms: float, metadata: Optional[Dict] = None):
    """
    Log performance metrics
    
    Args:
        operation: Name of operation (e.g., "database_query", "ai_generation")
        duration_ms: Time taken in milliseconds
        metadata: Additional context
    """
    meta_str = f" | {metadata}" if metadata else ""
    logger.info(f"⚡ PERFORMANCE | {operation} | {duration_ms:.2f}ms{meta_str}")


def log_user_action(user_id: int, action: str, details: Optional[Dict] = None):
    """
    Log user actions for analytics
    
    Examples:
        - User logged in
        - Lead added
        - Message generated
        - Property viewed
    """
    details_str = f" | {details}" if details else ""
    logger.info(f"👤 USER_ACTION | user_id={user_id} | {action}{details_str}")
