#!/bin/bash

# Fix Telegram 409 Conflict - Stop all bot instances and restart cleanly

echo "🔍 Checking running backend containers..."
docker ps -a | grep backend

echo ""
echo "🛑 Stopping ALL backend containers..."
docker-compose down

echo ""
echo "⏳ Waiting 5 seconds for cleanup..."
sleep 5

echo ""
echo "🧹 Removing old containers..."
docker-compose rm -f backend

echo ""
echo "🔄 Starting backend with fresh instance..."
docker-compose up -d backend

echo ""
echo "⏳ Waiting 10 seconds for bot initialization..."
sleep 10

echo ""
echo "📋 Checking logs for Telegram bot startup..."
docker-compose logs --tail=50 backend | grep -E "Bot started|409|Conflict|getUpdates"

echo ""
echo "✅ Bot should be running cleanly now!"
echo "📱 Test by sending /start to @TaranteenBot"
