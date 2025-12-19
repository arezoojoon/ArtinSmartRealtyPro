"""
Migration: Add waha_session_name to tenants table
Run this SQL on your PostgreSQL database
"""

-- Add column
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS waha_session_name VARCHAR(100);

-- Add unique constraint
ALTER TABLE tenants ADD CONSTRAINT uix_tenant_waha_session UNIQUE (waha_session_name);

-- Auto-generate session names for existing tenants (optional)
UPDATE tenants 
SET waha_session_name = 'tenant_' || id::text 
WHERE waha_session_name IS NULL AND id IS NOT NULL;

-- Verify
SELECT id, name, email, waha_session_name FROM tenants;
