"""
Setup Telegram Webhook for ArtinSmartRealty
This script configures the webhook URL for your Telegram bot
"""

import asyncio
import sys
import os
import requests

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import async_session, Tenant, init_db
from sqlalchemy.future import select


def set_telegram_webhook(bot_token: str, webhook_url: str) -> bool:
    """Set webhook for a Telegram bot."""
    
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    payload = {
        "url": webhook_url,
        "drop_pending_updates": True
    }
    
    try:
        response = requests.post(api_url, json=payload)
        result = response.json()
        
        if result.get("ok"):
            print(f"✅ Webhook set successfully: {webhook_url}")
            return True
        else:
            print(f"❌ Failed to set webhook: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_webhook_info(bot_token: str):
    """Get current webhook info for a bot."""
    
    api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(api_url)
        result = response.json()
        
        if result.get("ok"):
            info = result.get("result", {})
            print("\n📡 Current Webhook Info:")
            print(f"   URL: {info.get('url', 'Not set')}")
            print(f"   Pending Updates: {info.get('pending_update_count', 0)}")
            if info.get('last_error_message'):
                print(f"   ⚠️  Last Error: {info.get('last_error_message')}")
        else:
            print(f"❌ Failed to get webhook info: {result.get('description')}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def setup_webhooks_for_all_tenants(domain: str):
    """Setup webhooks for all tenants with Telegram bots."""
    
    await init_db()
    
    async with async_session() as session:
        result = await session.execute(
            select(Tenant).where(
                Tenant.is_active == True,
                Tenant.telegram_bot_token.isnot(None)
            )
        )
        tenants = result.scalars().all()
        
        if not tenants:
            print("❌ No tenants with Telegram bots found!")
            return
        
        print(f"\n📱 Found {len(tenants)} tenant(s) with Telegram bots\n")
        
        for tenant in tenants:
            print(f"{'='*60}")
            print(f"Tenant: {tenant.name} (ID: {tenant.id})")
            print(f"{'='*60}")
            
            bot_token = tenant.telegram_bot_token
            webhook_url = f"https://{domain}/webhook/telegram/{bot_token}"
            
            # Get current webhook info
            get_webhook_info(bot_token)
            
            # Set new webhook
            print(f"\n🔧 Setting new webhook...")
            set_telegram_webhook(bot_token, webhook_url)
            
            print()


async def main():
    """Main function."""
    print("=" * 60)
    print("ArtinSmartRealty - Telegram Webhook Setup")
    print("=" * 60)
    
    # Get domain from user
    default_domain = "realty.artinsmartagent.com"
    domain = input(f"\nEnter your domain (default: {default_domain}): ").strip()
    
    if not domain:
        domain = default_domain
    
    print(f"\n🌐 Using domain: {domain}")
    
    # Setup webhooks
    await setup_webhooks_for_all_tenants(domain)
    
    print("\n" + "=" * 60)
    print("✅ Webhook setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test your bot on Telegram")
    print("2. Check webhook status: https://api.telegram.org/bot<TOKEN>/getWebhookInfo")
    print("3. View backend logs: docker compose logs backend -f")


if __name__ == "__main__":
    asyncio.run(main())
