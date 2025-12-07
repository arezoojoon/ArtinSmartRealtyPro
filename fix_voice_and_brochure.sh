#!/bin/bash
# Fix Voice Processing + brochure_pdf column on Production Server
# Run this script to fix both issues at once

echo "🚀 Deploying fixes to production..."

ssh root@srv1151343 << 'ENDSSH'

cd /root/ArtinSmartRealty

echo "📥 Step 1: Pull latest code from GitHub..."
git pull origin main

echo "🗄️ Step 2: Add missing brochure_pdf column..."
docker exec -i artinrealty-db psql -U postgres -d artinrealty << 'EOSQL'
ALTER TABLE tenant_properties ADD COLUMN IF NOT EXISTS brochure_pdf VARCHAR(512);
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tenant_properties' AND column_name = 'brochure_pdf';
EOSQL

echo "🔨 Step 3: Rebuild backend with FFmpeg (for voice processing)..."
docker-compose build --no-cache backend

echo "🔄 Step 4: Restart all services..."
docker-compose up -d

echo "⏳ Step 5: Wait for services to start..."
sleep 10

echo "✅ Step 6: Verify FFmpeg is installed in container..."
docker exec artinrealty-backend ffmpeg -version | head -n 1

echo "📊 Step 7: Check service health..."
docker-compose ps

echo ""
echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""
echo "🔍 To check logs:"
echo "   docker-compose logs -f backend"
echo ""
echo "🧪 To test voice processing:"
echo "   Send a voice message to @MokharidxbBot"
echo ""

ENDSSH

echo ""
echo "🎉 All fixes deployed successfully!"
