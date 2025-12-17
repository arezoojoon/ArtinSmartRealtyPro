-- Migration: Add booking and contact fields to tenants table
-- Date: 2025-12-14
-- Description: Add booking_url, contact_phone, whatsapp_link for per-tenant scheduling

-- Add new columns
ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS booking_url VARCHAR(512),
ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS whatsapp_link VARCHAR(512);

-- Update existing taranteen tenant with current values
UPDATE tenants 
SET 
    booking_url = 'https://calendly.com/taranteen-realty/consultation',
    contact_phone = '+971 50 503 7158',
    whatsapp_link = 'https://wa.me/971505037158'
WHERE name = 'taranteen' OR id = 1;

-- Verify
SELECT id, name, booking_url, contact_phone, whatsapp_link FROM tenants;
