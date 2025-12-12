#!/bin/bash

echo "🔍 Getting WhatsApp QR Code"
echo "==========================="
echo ""

API_KEY="0e86a8c2dd774defb6d2da56b409bb89"

# Get QR as base64 image
QR_DATA=$(curl -s -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default/auth/qr)

echo "QR Code Data (base64 image):"
echo "$QR_DATA"
echo ""

# Save to file
echo "$QR_DATA" > /tmp/whatsapp_qr.txt

echo "✅ QR code saved to /tmp/whatsapp_qr.txt"
echo ""
echo "📱 To view QR code:"
echo "1. Copy the base64 string from /tmp/whatsapp_qr.txt"
echo "2. Go to: https://base64.guru/converter/decode/image"
echo "3. Paste and decode"
echo "4. Scan with WhatsApp"
echo ""
echo "OR access via browser (Chrome/Firefox):"
echo "   Open browser developer tools → Network tab → Copy as Base64"
echo ""
echo "Checking session status..."
curl -s -H "X-Api-Key: $API_KEY" http://localhost:3002/api/sessions/default | jq
