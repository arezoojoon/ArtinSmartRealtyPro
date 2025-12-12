"""
Email Notification System
Sends automated emails for subscription events
"""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timedelta
import os


class EmailConfig:
    """Email configuration"""
    # SMTP Settings
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "noreply@artinsmartrealty.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_app_password")
    SMTP_FROM_NAME = "ArtinSmartRealty"
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@artinsmartrealty.com")
    
    # Enable/Disable emails
    EMAILS_ENABLED = os.getenv("EMAILS_ENABLED", "true").lower() == "true"


class EmailTemplates:
    """Email templates"""
    
    @staticmethod
    def welcome_email(name: str, plan: str, trial_days: int) -> tuple[str, str]:
        """Welcome email after registration"""
        subject = f"Welcome to ArtinSmartRealty - Your {plan.capitalize()} Trial Started! 🚀"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #667eea;">Welcome to ArtinSmartRealty! 🎉</h1>
                
                <p>Hi {name},</p>
                
                <p>Thank you for joining <strong>ArtinSmartRealty</strong>! Your <strong>{plan.capitalize()} Plan</strong> trial has been activated.</p>
                
                <div style="background: #f0f4ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #667eea;">Your Trial Details:</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li>✅ Plan: <strong>{plan.capitalize()}</strong></li>
                        <li>⏰ Trial Duration: <strong>{trial_days} days</strong></li>
                        <li>🎯 Full Access: <strong>All features included</strong></li>
                    </ul>
                </div>
                
                <h3>What's Next?</h3>
                <ol>
                    <li>Login to your dashboard</li>
                    <li>Setup your AI bot (WhatsApp/Telegram)</li>
                    <li>Add your properties</li>
                    <li>Start engaging with leads!</li>
                </ol>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.artinsmartrealty.com/dashboard" 
                       style="background: #667eea; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 8px; display: inline-block;">
                        Go to Dashboard
                    </a>
                </div>
                
                <p>Need help? Reply to this email or contact our support team.</p>
                
                <p>Best regards,<br>
                The ArtinSmartRealty Team</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="font-size: 12px; color: #999;">
                    ArtinSmartRealty - AI-Powered Real Estate Sales Automation<br>
                    © 2025 All rights reserved
                </p>
            </div>
        </body>
        </html>
        """
        
        return subject, html
    
    @staticmethod
    def trial_ending_soon(name: str, plan: str, days_left: int, trial_ends_at: datetime) -> tuple[str, str]:
        """Email when trial is ending soon (3 days before)"""
        subject = f"⏰ Your {plan.capitalize()} Trial Ends in {days_left} Days"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f59e0b;">Your Trial is Ending Soon ⏰</h1>
                
                <p>Hi {name},</p>
                
                <p>Your <strong>{plan.capitalize()} Plan</strong> trial will expire in <strong>{days_left} day{'s' if days_left > 1 else ''}</strong>.</p>
                
                <div style="background: #fef3c7; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                    <h3 style="margin-top: 0; color: #92400e;">Trial Expiry:</h3>
                    <p style="font-size: 18px; margin: 0;">
                        <strong>{trial_ends_at.strftime('%B %d, %Y at %I:%M %p')}</strong>
                    </p>
                </div>
                
                <p>Don't lose access to your AI-powered sales automation!</p>
                
                <h3>Continue with {plan.capitalize()} Plan:</h3>
                <ul>
                    {"<li>💰 <strong>$99/month</strong> or <strong>$999/year</strong> (save 17%)</li>" if plan == "basic" else 
                     "<li>💰 <strong>$199/month</strong> or <strong>$1,999/year</strong> (save 17%)</li>"}
                    <li>🚀 No interruption in service</li>
                    <li>📊 Keep all your data and conversations</li>
                    <li>✨ Unlock advanced features</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.artinsmartrealty.com/subscription/pricing" 
                       style="background: #10b981; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; display: inline-block; font-size: 18px;">
                        Subscribe Now
                    </a>
                </div>
                
                <p>Questions? We're here to help!</p>
                
                <p>Best regards,<br>
                The ArtinSmartRealty Team</p>
            </div>
        </body>
        </html>
        """
        
        return subject, html
    
    @staticmethod
    def trial_expired(name: str, plan: str) -> tuple[str, str]:
        """Email when trial expires"""
        subject = "Your Trial Has Expired - Subscribe to Continue"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #ef4444;">Your Trial Has Expired</h1>
                
                <p>Hi {name},</p>
                
                <p>Your <strong>{plan.capitalize()} Plan</strong> trial has ended.</p>
                
                <div style="background: #fee2e2; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <p style="margin: 0; color: #991b1b;">
                        ⚠️ Your account is currently inactive. Subscribe now to restore access.
                    </p>
                </div>
                
                <p>We hope you enjoyed your trial! Here's what you're missing:</p>
                
                <ul>
                    <li>🤖 AI-powered chatbots for WhatsApp & Telegram</li>
                    <li>📧 Automated follow-up campaigns</li>
                    <li>📊 Lead scoring and analytics</li>
                    <li>📅 Appointment scheduling</li>
                    {"<li>🔍 LinkedIn Lead Scraper (Pro only)</li>" if plan == "pro" else ""}
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.artinsmartrealty.com/subscription/pricing" 
                       style="background: #667eea; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; display: inline-block; font-size: 18px;">
                        Reactivate Your Account
                    </a>
                </div>
                
                <p>Your data is safe and will be preserved for 30 days.</p>
                
                <p>Best regards,<br>
                The ArtinSmartRealty Team</p>
            </div>
        </body>
        </html>
        """
        
        return subject, html
    
    @staticmethod
    def payment_successful(name: str, plan: str, amount: float, currency: str, 
                          next_payment_date: datetime, billing_cycle: str) -> tuple[str, str]:
        """Email after successful payment"""
        subject = f"Payment Successful - {plan.capitalize()} Subscription Active! ✅"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Payment Successful! ✅</h1>
                
                <p>Hi {name},</p>
                
                <p>Thank you! Your payment has been processed successfully.</p>
                
                <div style="background: #d1fae5; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #065f46;">Subscription Details:</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Plan:</strong> {plan.capitalize()}</li>
                        <li><strong>Amount Paid:</strong> {currency} {amount:,.2f}</li>
                        <li><strong>Billing:</strong> {billing_cycle.capitalize()}</li>
                        <li><strong>Next Payment:</strong> {next_payment_date.strftime('%B %d, %Y')}</li>
                    </ul>
                </div>
                
                <p>Your subscription is now active with full access to all features!</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.artinsmartrealty.com/dashboard" 
                       style="background: #667eea; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 8px; display: inline-block;">
                        Go to Dashboard
                    </a>
                </div>
                
                <p>Need help? Contact support anytime.</p>
                
                <p>Best regards,<br>
                The ArtinSmartRealty Team</p>
            </div>
        </body>
        </html>
        """
        
        return subject, html
    
    @staticmethod
    def payment_failed(name: str, plan: str, amount: float, reason: str) -> tuple[str, str]:
        """Email when payment fails"""
        subject = "⚠️ Payment Failed - Action Required"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #ef4444;">Payment Failed ⚠️</h1>
                
                <p>Hi {name},</p>
                
                <p>We were unable to process your payment for the <strong>{plan.capitalize()} Plan</strong>.</p>
                
                <div style="background: #fee2e2; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <p style="margin: 0; color: #991b1b;">
                        <strong>Reason:</strong> {reason}
                    </p>
                </div>
                
                <p>Please update your payment method or try again.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.artinsmartrealty.com/subscription/payment" 
                       style="background: #ef4444; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 8px; display: inline-block;">
                        Retry Payment
                    </a>
                </div>
                
                <p>If you continue to experience issues, please contact our support team.</p>
                
                <p>Best regards,<br>
                The ArtinSmartRealty Team</p>
            </div>
        </body>
        </html>
        """
        
        return subject, html
    
    @staticmethod
    def subscription_renewed(name: str, plan: str, next_payment_date: datetime) -> tuple[str, str]:
        """Email when subscription auto-renews"""
        subject = f"Subscription Renewed - {plan.capitalize()} Plan"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Subscription Renewed ✅</h1>
                
                <p>Hi {name},</p>
                
                <p>Your <strong>{plan.capitalize()} Plan</strong> subscription has been automatically renewed.</p>
                
                <div style="background: #d1fae5; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <p style="margin: 0;">
                        <strong>Next Payment Date:</strong> {next_payment_date.strftime('%B %d, %Y')}
                    </p>
                </div>
                
                <p>Your service continues uninterrupted. Thank you for staying with us!</p>
                
                <p>Best regards,<br>
                The ArtinSmartRealty Team</p>
            </div>
        </body>
        </html>
        """
        
        return subject, html


class EmailService:
    """Email sending service"""
    
    @staticmethod
    async def send_email(to_email: str, subject: str, html_content: str) -> bool:
        """
        Send email asynchronously
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content
            
        Returns:
            True if sent successfully
        """
        
        if not EmailConfig.EMAILS_ENABLED:
            print(f"[EMAIL DISABLED] Would send to {to_email}: {subject}")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{EmailConfig.SMTP_FROM_NAME} <{EmailConfig.SMTP_FROM_EMAIL}>"
            msg['To'] = to_email
            
            # Attach HTML
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send via SMTP
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _send_smtp, msg, to_email)
            
            print(f"[EMAIL SENT] To: {to_email}, Subject: {subject}")
            return True
            
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send to {to_email}: {str(e)}")
            return False


def _send_smtp(msg: MIMEMultipart, to_email: str):
    """Synchronous SMTP sending (called in executor)"""
    with smtplib.SMTP(EmailConfig.SMTP_HOST, EmailConfig.SMTP_PORT) as server:
        server.starttls()
        server.login(EmailConfig.SMTP_USER, EmailConfig.SMTP_PASSWORD)
        server.send_message(msg)


# ==================== HELPER FUNCTIONS ====================

async def send_welcome_email(name: str, email: str, plan: str, trial_days: int):
    """Send welcome email after registration"""
    subject, html = EmailTemplates.welcome_email(name, plan, trial_days)
    await EmailService.send_email(email, subject, html)


async def send_trial_ending_email(name: str, email: str, plan: str, days_left: int, trial_ends_at: datetime):
    """Send trial ending reminder"""
    subject, html = EmailTemplates.trial_ending_soon(name, plan, days_left, trial_ends_at)
    await EmailService.send_email(email, subject, html)


async def send_trial_expired_email(name: str, email: str, plan: str):
    """Send trial expired notification"""
    subject, html = EmailTemplates.trial_expired(name, plan)
    await EmailService.send_email(email, subject, html)


async def send_payment_success_email(name: str, email: str, plan: str, amount: float, 
                                     currency: str, next_payment_date: datetime, billing_cycle: str):
    """Send payment successful confirmation"""
    subject, html = EmailTemplates.payment_successful(name, plan, amount, currency, next_payment_date, billing_cycle)
    await EmailService.send_email(email, subject, html)


async def send_payment_failed_email(name: str, email: str, plan: str, amount: float, reason: str):
    """Send payment failed notification"""
    subject, html = EmailTemplates.payment_failed(name, plan, amount, reason)
    await EmailService.send_email(email, subject, html)


async def send_subscription_renewed_email(name: str, email: str, plan: str, next_payment_date: datetime):
    """Send subscription renewal confirmation"""
    subject, html = EmailTemplates.subscription_renewed(name, plan, next_payment_date)
    await EmailService.send_email(email, subject, html)
