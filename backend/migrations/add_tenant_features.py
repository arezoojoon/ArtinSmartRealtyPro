"""
Migration: Add TenantFeature table for feature flags system

Run this SQL in your PostgreSQL database:
"""

CREATE_TENANT_FEATURES_TABLE = """
-- Create enum type for features (if not exists)
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
    is_enabled BOOLEAN DEFAULT TRUE,
    enabled_at TIMESTAMP DEFAULT NOW(),
    enabled_by INTEGER,
    notes VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint: one entry per tenant per feature
    CONSTRAINT uix_tenant_feature UNIQUE (tenant_id, feature)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_tenant_features_tenant_id ON tenant_features(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_features_enabled ON tenant_features(tenant_id, is_enabled);

-- Grant default features to all existing tenants
INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT 
    t.id,
    'telegram_bot'::featureflag,
    TRUE,
    'Auto-enabled for all existing tenants'
FROM tenants t
ON CONFLICT (tenant_id, feature) DO NOTHING;

INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT 
    t.id,
    'multi_language'::featureflag,
    TRUE,
    'Auto-enabled for all existing tenants'
FROM tenants t
ON CONFLICT (tenant_id, feature) DO NOTHING;

INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT 
    t.id,
    'calendar_booking'::featureflag,
    TRUE,
    'Auto-enabled for all existing tenants'
FROM tenants t
ON CONFLICT (tenant_id, feature) DO NOTHING;

INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT 
    t.id,
    'broadcast_messages'::featureflag,
    TRUE,
    'Auto-enabled for all existing tenants'
FROM tenants t
ON CONFLICT (tenant_id, feature) DO NOTHING;

-- Auto-enable RAG system for all tenants (since we just built it!)
INSERT INTO tenant_features (tenant_id, feature, is_enabled, notes)
SELECT 
    t.id,
    'rag_system'::featureflag,
    TRUE,
    'Auto-enabled - new feature available for all'
FROM tenants t
ON CONFLICT (tenant_id, feature) DO NOTHING;
"""

if __name__ == "__main__":
    print("📋 Migration SQL for tenant_features table:")
    print("=" * 80)
    print(CREATE_TENANT_FEATURES_TABLE)
    print("=" * 80)
    print("\n✅ Copy and run this SQL in your PostgreSQL database")
    print("   Or run: docker-compose exec db psql -U postgres -d realty_db")
    print("   Then paste the SQL above\n")
