-- Migration: Add filled_slots and pending_slot to Lead model
-- Date: 2025-01-XX
-- Purpose: Support new slot-filling state machine

ALTER TABLE lead
ADD COLUMN IF NOT EXISTS filled_slots JSONB DEFAULT '{}';

ALTER TABLE lead
ADD COLUMN IF NOT EXISTS pending_slot VARCHAR(50);

-- Update existing leads to have empty filled_slots
UPDATE lead
SET filled_slots = '{}'::jsonb
WHERE filled_slots IS NULL;
