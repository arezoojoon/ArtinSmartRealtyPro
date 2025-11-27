-- Migration: Add context fields to Lead table
-- Date: 2025-11-28
-- Description: Add filled_slots (JSONB) and pending_slot (VARCHAR) for bot context management

-- Add filled_slots column
ALTER TABLE lead ADD COLUMN IF NOT EXISTS filled_slots JSONB DEFAULT '{}';

-- Add pending_slot column
ALTER TABLE lead ADD COLUMN IF NOT EXISTS pending_slot VARCHAR(50);

-- Create index on filled_slots for faster JSON queries
CREATE INDEX IF NOT EXISTS idx_lead_filled_slots ON lead USING GIN (filled_slots);

-- Verify columns were added
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'lead' 
AND column_name IN ('filled_slots', 'pending_slot');
