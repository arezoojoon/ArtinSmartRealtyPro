#!/bin/bash
# Quick deployment script to fix brain.py on production server
# Run this ON THE SERVER (not locally)

cd /opt/ArtinSmartRealty

echo "🔄 Pulling latest code from repository..."
# If you have git setup:
# git pull origin main

echo "🛑 Stopping backend container..."
docker-compose stop backend

echo "🔨 Rebuilding backend with updated brain.py..."
docker-compose build --no-cache backend

echo "🚀 Starting backend..."
docker-compose up -d backend

echo "📊 Checking backend status..."
sleep 5
docker-compose ps backend

echo "📝 Viewing recent logs..."
docker-compose logs --tail=50 backend | grep -E "✅|❌|Bot started|GEMINI"

echo ""
echo "🎉 Deployment complete!"
echo "Test the bot now: Send /start to @TaranteenBot"
