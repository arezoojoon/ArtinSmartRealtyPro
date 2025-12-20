#!/bin/bash
# REAL TELEGRAM BOT TEST - Send actual message and check response

BOT_TOKEN="8541904612:AAFxZ_nOW8HHHfCgORGSHwH9E00Qt83EBgw"

echo "=== TESTING TELEGRAM BOT - @TaranteenrealstateBot ==="
echo ""

# 1. Check bot info
echo "1. Bot Info:"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe" | python3 -m json.tool
echo ""

# 2. Get updates (check if bot receives messages)
echo "2. Recent Messages:"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates?limit=5" | python3 -m json.tool
echo ""

# 3. Check webhook status
echo "3. Webhook Status:"
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool
echo ""

echo "=== TEST INSTRUCTIONS ==="
echo ""
echo "To REALLY test the bot:"
echo "1. Open Telegram"
echo "2. Search: @TaranteenrealstateBot"
echo "3. Send: /start"
echo "4. Check if bot responds"
echo ""
echo "If no response, check:"
echo "  - docker-compose logs -f backend | grep Telegram"
echo "  - docker-compose logs -f backend | grep ERROR"
