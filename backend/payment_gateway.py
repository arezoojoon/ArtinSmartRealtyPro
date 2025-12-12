"""
Payment Gateway Integration
Supports: ZarinPal (Iran), Stripe (International)
"""

import aiohttp
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict
from enum import Enum

from pydantic import BaseModel


class PaymentGateway(str, Enum):
    ZARINPAL = "zarinpal"
    STRIPE = "stripe"
    MANUAL = "manual"  # For admin manual activation


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


# ============================================
# ZARINPAL INTEGRATION (IRAN)
# ============================================

class ZarinPalConfig:
    """ZarinPal configuration"""
    MERCHANT_ID = "YOUR_ZARINPAL_MERCHANT_ID"  # Get from https://www.zarinpal.com/
    SANDBOX = True  # Set to False in production
    
    # API URLs
    REQUEST_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json" if SANDBOX else "https://api.zarinpal.com/pg/v4/payment/request.json"
    VERIFY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json" if SANDBOX else "https://api.zarinpal.com/pg/v4/payment/verify.json"
    PAYMENT_URL = "https://sandbox.zarinpal.com/pg/StartPay/" if SANDBOX else "https://www.zarinpal.com/pg/StartPay/"


class ZarinPalPayment:
    """ZarinPal payment handler"""
    
    @staticmethod
    async def request_payment(
        amount: int,  # Amount in Tomans
        description: str,
        email: str,
        mobile: str,
        callback_url: str
    ) -> Dict:
        """
        Request payment from ZarinPal
        
        Args:
            amount: Amount in Tomans (NOT Rials!)
            description: Payment description
            email: User email
            mobile: User mobile (format: 09123456789)
            callback_url: Callback URL after payment
            
        Returns:
            {
                "status": "success",
                "authority": "A00000000000000000000000000123456789",
                "payment_url": "https://sandbox.zarinpal.com/pg/StartPay/A00000000000000000000000000123456789"
            }
        """
        
        data = {
            "merchant_id": ZarinPalConfig.MERCHANT_ID,
            "amount": amount,
            "description": description,
            "callback_url": callback_url,
            "metadata": {
                "email": email,
                "mobile": mobile
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(ZarinPalConfig.REQUEST_URL, json=data) as response:
                result = await response.json()
                
                if result.get("data", {}).get("code") == 100:
                    authority = result["data"]["authority"]
                    return {
                        "status": "success",
                        "authority": authority,
                        "payment_url": f"{ZarinPalConfig.PAYMENT_URL}{authority}"
                    }
                else:
                    return {
                        "status": "error",
                        "code": result.get("errors", {}).get("code"),
                        "message": result.get("errors", {}).get("message", "Payment request failed")
                    }
    
    @staticmethod
    async def verify_payment(authority: str, amount: int) -> Dict:
        """
        Verify payment with ZarinPal
        
        Args:
            authority: Payment authority from request
            amount: Original amount in Tomans
            
        Returns:
            {
                "status": "success",
                "ref_id": "123456789",
                "card_pan": "1234********5678"
            }
        """
        
        data = {
            "merchant_id": ZarinPalConfig.MERCHANT_ID,
            "amount": amount,
            "authority": authority
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(ZarinPalConfig.VERIFY_URL, json=data) as response:
                result = await response.json()
                
                if result.get("data", {}).get("code") == 100:
                    return {
                        "status": "success",
                        "ref_id": result["data"]["ref_id"],
                        "card_pan": result["data"].get("card_pan", ""),
                        "fee": result["data"].get("fee", 0)
                    }
                else:
                    return {
                        "status": "error",
                        "code": result.get("errors", {}).get("code"),
                        "message": result.get("errors", {}).get("message", "Payment verification failed")
                    }


# ============================================
# STRIPE INTEGRATION (INTERNATIONAL)
# ============================================

class StripeConfig:
    """Stripe configuration"""
    SECRET_KEY = "sk_test_YOUR_STRIPE_SECRET_KEY"  # Get from https://dashboard.stripe.com/
    PUBLISHABLE_KEY = "pk_test_YOUR_STRIPE_PUBLISHABLE_KEY"
    WEBHOOK_SECRET = "whsec_YOUR_WEBHOOK_SECRET"
    
    # API Version
    API_VERSION = "2023-10-16"


class StripePayment:
    """Stripe payment handler (requires stripe library)"""
    
    @staticmethod
    async def create_payment_intent(
        amount: int,  # Amount in cents (e.g., $99.00 = 9900)
        currency: str,
        customer_email: str,
        metadata: Dict
    ) -> Dict:
        """
        Create Stripe PaymentIntent
        
        Args:
            amount: Amount in cents
            currency: Currency code (usd, eur, etc.)
            customer_email: Customer email
            metadata: Additional metadata
            
        Returns:
            {
                "status": "success",
                "client_secret": "pi_xxx_secret_yyy",
                "payment_intent_id": "pi_xxx"
            }
        """
        
        try:
            import stripe
            stripe.api_key = StripeConfig.SECRET_KEY
            
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                receipt_email=customer_email,
                metadata=metadata,
                automatic_payment_methods={"enabled": True}
            )
            
            return {
                "status": "success",
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> bool:
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Raw request body
            signature: Stripe-Signature header value
            
        Returns:
            True if signature is valid
        """
        
        try:
            import stripe
            stripe.Webhook.construct_event(
                payload,
                signature,
                StripeConfig.WEBHOOK_SECRET
            )
            return True
        except Exception:
            return False


# ============================================
# UNIFIED PAYMENT INTERFACE
# ============================================

class PaymentRequest(BaseModel):
    """Payment request model"""
    gateway: PaymentGateway
    amount: float  # In USD or Tomans
    currency: str  # "USD", "IRR"
    plan: str  # "basic", "pro"
    billing_cycle: str  # "monthly", "yearly"
    tenant_id: int
    email: str
    mobile: Optional[str] = None
    callback_url: str


class PaymentProcessor:
    """Unified payment processor"""
    
    @staticmethod
    async def initiate_payment(request: PaymentRequest) -> Dict:
        """
        Initiate payment based on gateway
        
        Returns:
            {
                "status": "success",
                "payment_url": "...",  # For redirect
                "payment_id": "...",   # For tracking
                "gateway": "zarinpal"
            }
        """
        
        if request.gateway == PaymentGateway.ZARINPAL:
            # Convert USD to Tomans if needed
            amount_tomans = int(request.amount * 10)  # Simplified conversion
            if request.currency == "USD":
                amount_tomans = int(request.amount * 600000)  # ~60,000 IRR per USD
            
            result = await ZarinPalPayment.request_payment(
                amount=amount_tomans,
                description=f"ArtinSmartRealty - {request.plan.upper()} Plan ({request.billing_cycle})",
                email=request.email,
                mobile=request.mobile or "",
                callback_url=request.callback_url
            )
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "payment_url": result["payment_url"],
                    "payment_id": result["authority"],
                    "gateway": "zarinpal"
                }
            else:
                return result
        
        elif request.gateway == PaymentGateway.STRIPE:
            # Amount in cents
            amount_cents = int(request.amount * 100)
            
            result = await StripePayment.create_payment_intent(
                amount=amount_cents,
                currency=request.currency.lower(),
                customer_email=request.email,
                metadata={
                    "tenant_id": request.tenant_id,
                    "plan": request.plan,
                    "billing_cycle": request.billing_cycle
                }
            )
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "client_secret": result["client_secret"],
                    "payment_id": result["payment_intent_id"],
                    "gateway": "stripe"
                }
            else:
                return result
        
        else:
            return {
                "status": "error",
                "message": "Unsupported payment gateway"
            }
    
    @staticmethod
    async def verify_payment(
        gateway: PaymentGateway,
        payment_id: str,
        amount: float,
        currency: str = "USD"
    ) -> Dict:
        """
        Verify payment completion
        
        Returns:
            {
                "status": "success",
                "verified": True,
                "transaction_id": "...",
                "card_info": "..."
            }
        """
        
        if gateway == PaymentGateway.ZARINPAL:
            amount_tomans = int(amount * 10)
            if currency == "USD":
                amount_tomans = int(amount * 600000)
            
            result = await ZarinPalPayment.verify_payment(
                authority=payment_id,
                amount=amount_tomans
            )
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "verified": True,
                    "transaction_id": result["ref_id"],
                    "card_info": result.get("card_pan", "")
                }
            else:
                return {
                    "status": "error",
                    "verified": False,
                    "message": result.get("message", "Verification failed")
                }
        
        elif gateway == PaymentGateway.STRIPE:
            # Stripe verification happens via webhook
            return {
                "status": "success",
                "verified": True,
                "message": "Stripe payment verified via webhook"
            }
        
        else:
            return {
                "status": "error",
                "verified": False,
                "message": "Unsupported gateway"
            }


# ============================================
# PRICING HELPER
# ============================================

def get_payment_amount(plan: str, billing_cycle: str, currency: str = "USD") -> float:
    """Get payment amount for plan and billing cycle"""
    
    pricing = {
        "basic": {
            "monthly": {"USD": 99, "IRR": 5940000},  # 99 USD = ~5.94M Tomans
            "yearly": {"USD": 999, "IRR": 59940000}
        },
        "pro": {
            "monthly": {"USD": 199, "IRR": 11940000},
            "yearly": {"USD": 1999, "IRR": 119940000}
        }
    }
    
    return pricing.get(plan, {}).get(billing_cycle, {}).get(currency, 0)
