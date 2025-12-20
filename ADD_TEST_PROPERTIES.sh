#!/bin/bash
# ADD TEST PROPERTIES - Bot needs properties to work!

echo "=== ADDING TEST PROPERTIES FOR TENANT ==="
echo ""

cd /opt/ArtinSmartRealty

# Add 3 sample properties
docker-compose exec -T db psql -U postgres -d artinrealty << 'EOF'
-- Add sample properties for tenant 1
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type, 
    location, price, currency, bedrooms, bathrooms, 
    area_sqft, description, is_available, created_at, updated_at
) VALUES 
(
    1, 
    'Luxury Villa in Dubai Marina', 
    'villa', 
    'sale', 
    'Dubai Marina', 
    2500000, 
    'AED', 
    4, 
    5, 
    3500, 
    'Stunning 4-bedroom villa with sea view, private pool, and modern amenities', 
    true, 
    NOW(), 
    NOW()
),
(
    1, 
    'Modern Apartment in Downtown', 
    'apartment', 
    'rent', 
    'Downtown Dubai', 
    8000, 
    'AED', 
    2, 
    2, 
    1200, 
    'Fully furnished 2-bedroom apartment near Burj Khalifa', 
    true, 
    NOW(), 
    NOW()
),
(
    1, 
    'Penthouse with Burj View', 
    'penthouse', 
    'sale', 
    'Business Bay', 
    5000000, 
    'AED', 
    3, 
    4, 
    2800, 
    'Exclusive penthouse with panoramic Burj Khalifa view', 
    true, 
    NOW(), 
    NOW()
);

-- Verify
SELECT id, name, transaction_type, price, currency, location FROM tenant_properties;
EOF

echo ""
echo "=== PROPERTIES ADDED ==="
echo ""
echo "Now restart backend to reload properties:"
echo "  docker-compose restart backend"
echo ""
echo "Then test bot again:"
echo "  1. Send message to @TaranteenrealstateBot"
echo "  2. Ask: 'I want to buy a villa'"
echo "  3. Check if bot suggests properties"
