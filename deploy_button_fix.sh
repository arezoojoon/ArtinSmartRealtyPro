#!/bin/bash

# ============================================
# Deploy Button Format Fix + Gemini API Key
# ============================================

echo "🚀 Starting deployment..."

# Step 1: Pull latest code
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Step 2: Check if .env has Gemini API key
echo "🔑 Checking Gemini API configuration..."
if grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env; then
    echo "⚠️  WARNING: Gemini API key is not configured!"
    echo "   Please update .env with your actual API key from:"
    echo "   https://aistudio.google.com/app/apikey"
    echo ""
    echo "   Current line in .env:"
    grep "GEMINI_API_KEY" .env
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

# Step 3: Rebuild backend container
echo "🔨 Rebuilding backend container..."
docker-compose up -d --build backend

# Step 4: Check container status
echo "✅ Checking container health..."
sleep 3
docker-compose ps backend

# Step 5: Show recent logs
echo "📋 Recent backend logs:"
docker-compose logs --tail=50 backend | grep -E "(ERROR|INFO|Button|GEMINI)"

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📝 Next steps:"
echo "   1. Update .env with real Gemini API key if not done"
echo "   2. Test bot: /start in Telegram"
echo "   3. Share contact → should show 3 purpose buttons"
echo "   4. Send voice message → should transcribe with Gemini"
echo ""
