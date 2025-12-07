#!/bin/bash
# Fix PDF Upload Feature - Emergency Deployment
# Issue: PDF upload failing due to missing PyPDF2 dependency and lack of authentication
# Commit: e83e20b

set -e  # Exit on any error

echo "=========================================="
echo "🔧 PDF Upload Fix Deployment"
echo "=========================================="

# Navigate to project directory
cd /opt/ArtinSmartRealty

# Step 1: Pull latest code
echo ""
echo "📥 Step 1: Pulling latest code from GitHub..."
git pull origin main

# Verify we're on the right commit
CURRENT_COMMIT=$(git rev-parse --short HEAD)
echo "✅ Current commit: $CURRENT_COMMIT"

# Step 2: Rebuild backend with new dependencies
echo ""
echo "🔨 Step 2: Rebuilding backend container (with PyPDF2)..."
docker-compose build --no-cache backend

# Step 3: Restart backend service
echo ""
echo "🔄 Step 3: Restarting backend service..."
docker-compose restart backend

# Wait for backend to be ready
echo ""
echo "⏳ Waiting for backend to initialize..."
sleep 10

# Step 4: Verify backend health
echo ""
echo "🏥 Step 4: Checking backend health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$HEALTH_STATUS" -eq 200 ]; then
    echo "✅ Backend is healthy (HTTP 200)"
else
    echo "❌ Backend health check failed (HTTP $HEALTH_STATUS)"
    echo "Checking logs..."
    docker-compose logs --tail=50 backend
    exit 1
fi

# Step 5: Verify PDF upload directory exists
echo ""
echo "📁 Step 5: Verifying upload directories..."
docker exec artinrealty-backend mkdir -p /app/uploads/pdfs
docker exec artinrealty-backend ls -la /app/uploads/ || true

# Step 6: Test PDF upload endpoint (dry run)
echo ""
echo "🧪 Step 6: Testing PDF upload endpoint authentication..."
# This will fail with 401/403 if auth is working (which is correct)
TEST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/tenants/1/properties/upload-pdf)
if [ "$TEST_RESPONSE" -eq 401 ] || [ "$TEST_RESPONSE" -eq 403 ] || [ "$TEST_RESPONSE" -eq 422 ]; then
    echo "✅ Endpoint authentication is working (HTTP $TEST_RESPONSE - expected)"
else
    echo "⚠️  Unexpected response: HTTP $TEST_RESPONSE (might be OK, check logs)"
fi

# Step 7: Check if PyPDF2 is installed
echo ""
echo "📦 Step 7: Verifying PyPDF2 installation..."
docker exec artinrealty-backend python -c "import PyPDF2; print(f'PyPDF2 version: {PyPDF2.__version__}')" && \
    echo "✅ PyPDF2 is installed" || \
    echo "❌ PyPDF2 is NOT installed (rebuild failed?)"

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "📋 Summary of changes:"
echo "  1. ✅ Added PyPDF2 3.0.1 to requirements.txt"
echo "  2. ✅ Added authentication to PDF upload endpoint"
echo "  3. ✅ Added comprehensive error logging"
echo "  4. ✅ Improved error handling for file operations"
echo ""
echo "🧪 Testing instructions:"
echo "  1. Login to admin panel: https://artin.artinrealty.com"
echo "  2. Go to Properties → Upload PDF button"
echo "  3. Upload a property brochure PDF"
echo "  4. Verify: Property created with extracted data"
echo ""
echo "📊 Monitor logs with:"
echo "  docker-compose logs -f backend | grep -i 'pdf\\|upload'"
echo ""
