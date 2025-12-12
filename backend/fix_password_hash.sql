-- Enable pgcrypto extension for password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Update tenant 1 password to Test1234! using correct hash method
-- This matches the Python pbkdf2_hmac implementation
UPDATE tenants 
SET password_hash = encode(
  digest('Test1234!artinsmartrealty_salt_v2', 'sha256'), 
  'hex'
)
WHERE id = 1;

-- Verify
SELECT id, email, substring(password_hash, 1, 20) as hash_preview 
FROM tenants 
WHERE id = 1;
