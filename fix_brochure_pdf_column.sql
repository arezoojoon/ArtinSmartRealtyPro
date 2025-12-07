-- Fix missing brochure_pdf column for all tenants
-- Run this on production database

ALTER TABLE tenant_properties ADD COLUMN IF NOT EXISTS brochure_pdf VARCHAR(512);

-- Verify the column was added
\d tenant_properties;
