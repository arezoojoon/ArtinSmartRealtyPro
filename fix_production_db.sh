#!/bin/bash
# Fix Production Database - Add Missing Columns
# Run this script on the production server: bash fix_production_db.sh

set -e  # Exit on error

echo "🔧 Adding missing columns to production database..."

# Add admin_chat_id to tenants table
docker exec artinsmartrealty-db-1 psql -U postgres -d postgres -c \
  "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS admin_chat_id VARCHAR(255);"

echo "✅ Added admin_chat_id to tenants table"

# Add ghost_reminder_sent to leads table
docker exec artinsmartrealty-db-1 psql -U postgres -d postgres -c \
  "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ghost_reminder_sent BOOLEAN DEFAULT FALSE;"

echo "✅ Added ghost_reminder_sent to leads table"

# Verify columns exist
echo ""
echo "🔍 Verifying columns..."
docker exec artinsmartrealty-db-1 psql -U postgres -d postgres -c \
  "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tenants' AND column_name = 'admin_chat_id';"

docker exec artinsmartrealty-db-1 psql -U postgres -d postgres -c \
  "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'ghost_reminder_sent';"

echo ""
echo "✅ Database migration complete!"
echo ""
echo "🔄 Now restart the backend service:"
echo "   cd /opt/ArtinSmartRealty"
echo "   docker-compose restart backend"
