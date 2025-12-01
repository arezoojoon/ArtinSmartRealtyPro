-- Update WhatsApp access token for ArtinSmartRealty tenant
UPDATE tenants 
SET whatsapp_access_token = 'EAANG6FvXZC28BO5TM8qTvSiuuhMHjZC3uWqaZA0qZBuW2vF7gkFBVZAC2ysBh8nNWsVtJJxaXFlpLkgXy3D9kZCDGXMPHzB2vfVjnMNz5EXtEiRHIYcZCvIkYrqODGMNKqpYLucD3OhN4lmHrObjNIvBgWM6KbPfZAXLBcRZA7ZBHKQX3nZBbZAe8u',
    updated_at = NOW()
WHERE name = 'ArtinSmartRealty';

-- Verify update
SELECT id, name, whatsapp_phone_number_id, 
       LEFT(whatsapp_access_token, 20) || '...' as token_preview,
       updated_at
FROM tenants 
WHERE name = 'ArtinSmartRealty';
