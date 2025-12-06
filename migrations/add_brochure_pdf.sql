-- Add brochure_pdf column to tenant_properties table
ALTER TABLE tenant_properties 
ADD COLUMN IF NOT EXISTS brochure_pdf VARCHAR(512);

-- Add comment
COMMENT ON COLUMN tenant_properties.brochure_pdf IS 'URL to property brochure/flyer PDF file';
