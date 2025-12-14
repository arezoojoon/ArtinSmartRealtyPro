-- Fix NULL boolean values in tenant_properties table
-- This migration updates all NULL boolean fields to their proper defaults

UPDATE tenant_properties 
SET 
    is_urgent = COALESCE(is_urgent, false),
    is_featured = COALESCE(is_featured, false),
    is_available = COALESCE(is_available, true),
    golden_visa_eligible = COALESCE(golden_visa_eligible, false)
WHERE 
    is_urgent IS NULL 
    OR is_featured IS NULL 
    OR is_available IS NULL 
    OR golden_visa_eligible IS NULL;

-- Verify the update
SELECT 
    COUNT(*) as total_properties,
    SUM(CASE WHEN is_urgent IS NULL THEN 1 ELSE 0 END) as null_is_urgent,
    SUM(CASE WHEN is_featured IS NULL THEN 1 ELSE 0 END) as null_is_featured,
    SUM(CASE WHEN is_available IS NULL THEN 1 ELSE 0 END) as null_is_available,
    SUM(CASE WHEN golden_visa_eligible IS NULL THEN 1 ELSE 0 END) as null_golden_visa
FROM tenant_properties;
