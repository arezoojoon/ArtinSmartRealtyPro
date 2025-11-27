#!/bin/bash
# Set Telegram Webhook for ArtinSmartRealty
# Usage: ./set_webhook.sh <BOT_TOKEN> <DOMAIN>

BOT_TOKEN="${1:-7941411336:AAGpkPMhg5Wa5RkWDD06sM3UbJ5veWwVgSs}"
DOMAIN="${2:-realty.artinsmartagent.com}"

WEBHOOK_URL="https://${DOMAIN}/webhook/telegram/${BOT_TOKEN}"

echo "======================================"
echo "Setting Telegram Webhook"
echo "======================================"
echo "Bot Token: ${BOT_TOKEN:0:20}..."
echo "Domain: ${DOMAIN}"
echo "Webhook URL: ${WEBHOOK_URL}"
echo ""

# Set webhook
echo "Setting webhook..."
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"${WEBHOOK_URL}\",\"drop_pending_updates\":true}"

echo ""
echo ""

# Get webhook info
echo "Checking webhook status..."
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"

echo ""
echo ""
echo "======================================"
echo "✅ Done!"
echo "======================================"
echo ""
echo "Test your bot now:"
echo "1. Open Telegram"
echo "2. Search for your bot"
echo "3. Send: /start"
