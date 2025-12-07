#!/bin/bash

# SSH to production server and run migration
# Add COLLECTING_NAME to conversationstate enum

ssh root@srv1151343.hstgr.io << 'EOF'
cd /root/ArtinSmartRealty

# Pull latest code
git pull origin main

# Add enum value to PostgreSQL
docker-compose exec -T postgres psql -U artinrealty -d artinrealty -c "ALTER TYPE conversationstate ADD VALUE IF NOT EXISTS 'collecting_name';"

# Verify the change
docker-compose exec -T postgres psql -U artinrealty -d artinrealty -c "SELECT enum_range(NULL::conversationstate);"

# Restart backend to pick up changes
docker-compose restart backend telegram_bot

echo "✅ Migration complete! COLLECTING_NAME added to database."
EOF
