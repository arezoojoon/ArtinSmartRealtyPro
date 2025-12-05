#!/bin/bash
# Feature Flags Deployment Script
# Run this on production server: bash deploy_feature_flags.sh

echo "🔍 Step 1: Checking backend logs..."
docker-compose logs backend --tail 100

echo ""
echo "🗄️ Step 2: Finding correct database name..."
docker-compose exec db psql -U postgres -c "\l"

echo ""
echo "📊 Step 3: Checking if database exists..."
DB_NAME=$(docker-compose exec db psql -U postgres -lqt | cut -d \| -f 1 | grep -w postgres | head -1 | xargs)
echo "Using database: $DB_NAME"

echo ""
echo "🚀 Step 4: Running migration SQL..."
docker-compose exec -T db psql -U postgres << 'EOFMIGRATION'
-- Create enum type for features
DO $$ BEGIN
    CREATE TYPE featureflag AS ENUM (
        'rag_system',
        'voice_ai',
        'advanced_analytics',
        'whatsapp_bot',
        'telegram_bot',
        'broadcast_messages',
        'lottery_system',
        'calendar_booking',
        'lead_export',
        'api_access',
        'custom_branding',
        'multi_language'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create tenant_features table
CREATE TABLE IF NOT EXISTS tenant_features (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    feature featureflag NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    enabled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enabled_by INTEGER REFERENCES tenants(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, feature)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tenant_features_tenant_id ON tenant_features(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_features_enabled ON tenant_features(tenant_id, is_enabled);

-- Enable default features for all existing tenants
INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT 
    id,
    unnest(ARRAY['telegram_bot'::featureflag, 'multi_language'::featureflag, 'calendar_booking'::featureflag, 'broadcast_messages'::featureflag, 'rag_system'::featureflag]),
    true,
    'Auto-enabled during migration'
FROM tenants
ON CONFLICT (tenant_id, feature) DO NOTHING;
EOFMIGRATION

echo ""
echo "✅ Step 5: Verifying migration..."
docker-compose exec -T db psql -U postgres -c "SELECT * FROM tenant_features;"

echo ""
echo "🔄 Step 6: Restarting backend..."
docker-compose restart backend

echo ""
echo "⏳ Waiting for backend to start..."
sleep 10

echo ""
echo "🧪 Step 7: Testing Feature Flags API..."
curl -s https://realty.artinsmartagent.com/api/admin/features | head -20

echo ""
echo "✅ Deployment complete!"
