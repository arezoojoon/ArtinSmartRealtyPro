#!/usr/bin/env python3
"""
Find where the bot is actually running from
"""
import requests

# The bot token from logs
BOT_TOKEN = "7750551672:AAHaVtzQAo0WqAZ8YqFJLp2IldXq2MNDkSs"

print("🔍 Checking bot webhook/polling status...")

# Check bot info
try:
    response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
    if response.status_code == 200:
        bot_info = response.json()
        print(f"✅ Bot is valid:")
        print(f"   Username: @{bot_info['result']['username']}")
        print(f"   Name: {bot_info['result']['first_name']}")
    else:
        print(f"❌ Bot token invalid or expired:")
        print(response.text)
        
    # Check webhook
    response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
    if response.status_code == 200:
        webhook = response.json()
        print(f"\n📡 Webhook status:")
        print(f"   URL: {webhook['result'].get('url', 'NOT SET - Using polling')}")
        print(f"   Pending updates: {webhook['result'].get('pending_update_count', 0)}")
        print(f"   Last error: {webhook['result'].get('last_error_message', 'None')}")
        
except Exception as e:
    print(f"❌ Error: {e}")
