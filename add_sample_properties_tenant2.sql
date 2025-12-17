-- 🏠 اضافه کردن املاک نمونه برای tenant_id=2 (saman ahmadi)
-- این اسکریپت املاک تست برای بات @samanahmadi_Bot اضافه می‌کنه

-- 1. آپارتمان لوکس دبی مارینا (Golden Visa eligible)
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    image_urls, primary_image, 
    is_available, is_featured, is_urgent,
    created_at, updated_at
) VALUES (
    2, 
    'Sky Gardens - Marina Heights', 
    'APARTMENT', 
    'BUY',
    'Dubai Marina', 
    'Dubai Marina Walk, Dubai, UAE',
    2800000.0, 
    2240.0, 
    'AED',
    3, 
    4, 
    1250.0,
    '["Sea View", "High Floor", "Pool & Gym", "Covered Parking", "24/7 Security", "Smart Home", "Burj Khalifa View"]'::json,
    '🌊 Stunning 3-bedroom luxury apartment with panoramic sea and Burj Khalifa views. Premium finishes, spacious layout, and world-class amenities in the most prestigious tower of Dubai Marina.',
    10.5, 
    8.2,
    true,
    '[
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1200",
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1200",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1200",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1200",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200"
    ]'::json,
    'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1200',
    true, 
    true, 
    false,
    NOW(),
    NOW()
);

-- 2. تاون‌هاوس مدرن Arabian Ranches (Family Living)
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    image_urls, primary_image,
    is_available, is_featured, is_urgent,
    created_at, updated_at
) VALUES (
    2,
    'Arabian Ranches Luxury Villa',
    'TOWNHOUSE',
    'BUY',
    'Arabian Ranches',
    'Arabian Ranches 2, Dubai, UAE',
    3500000.0,
    1400.0,
    'AED',
    4,
    5,
    2500.0,
    '["Private Garden", "Garage", "Community Pool", "Kids Play Area", "Golf Course View", "Maid Room"]'::json,
    '🏡 Spacious 4-bedroom townhouse in gated community. Perfect for families seeking Dubai lifestyle with excellent schools nearby and premium amenities.',
    9.2,
    7.8,
    true,
    '[
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200",
        "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=1200",
        "https://images.unsplash.com/photo-1600573472592-401b489a3cdc?w=1200",
        "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=1200"
    ]'::json,
    'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200',
    true,
    true,
    true,
    NOW(),
    NOW()
);

-- 3. استودیو اقتصادی Business Bay (Investment)
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    image_urls, primary_image,
    is_available, is_featured, is_urgent,
    created_at, updated_at
) VALUES (
    2,
    'Business Bay Studio',
    'APARTMENT',
    'BUY',
    'Business Bay',
    'Business Bay, Dubai, UAE',
    650000.0,
    1625.0,
    'AED',
    1,
    1,
    400.0,
    '["Furnished", "Pool & Gym", "Metro Access", "Security", "Balcony"]'::json,
    '💼 High-ROI studio apartment in Business Bay. Fully furnished with immediate rental income. Perfect for investors seeking passive income.',
    12.5,
    11.0,
    false,
    '[
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1200",
        "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?w=1200",
        "https://images.unsplash.com/photo-1600566753151-384129cf4e3e?w=1200"
    ]'::json,
    'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1200',
    true,
    false,
    false,
    NOW(),
    NOW()
);

-- 4. ویلای مجلل Palm Jumeirah (Ultra Luxury)
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    image_urls, primary_image,
    is_available, is_featured, is_urgent,
    created_at, updated_at
) VALUES (
    2,
    'Palm Jumeirah Beachfront Villa',
    'VILLA',
    'BUY',
    'Palm Jumeirah',
    'Palm Jumeirah, Dubai, UAE',
    15000000.0,
    3000.0,
    'AED',
    6,
    7,
    5000.0,
    '["Private Beach", "Infinity Pool", "Cinema Room", "Elevator", "Staff Quarters", "Smart Home", "Dock"]'::json,
    '🏖️ Ultra-luxury 6-bedroom villa with private beach access on iconic Palm Jumeirah. The epitome of Dubai luxury living with breathtaking views and world-class amenities.',
    7.5,
    6.0,
    true,
    '[
        "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1200",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1200",
        "https://images.unsplash.com/photo-1600047509358-9dc75507daeb?w=1200"
    ]'::json,
    'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1200',
    true,
    true,
    true,
    NOW(),
    NOW()
);

-- 5. پنت‌هاوس Downtown Dubai (Investment + Living)
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    image_urls, primary_image,
    is_available, is_featured, is_urgent,
    created_at, updated_at
) VALUES (
    2,
    'Downtown Dubai Penthouse',
    'PENTHOUSE',
    'BUY',
    'Downtown Dubai',
    'Downtown Dubai, Dubai, UAE',
    8500000.0,
    4250.0,
    'AED',
    4,
    5,
    2000.0,
    '["Burj Khalifa View", "Private Terrace", "Jacuzzi", "Premium Finishes", "Concierge", "Valet Parking"]'::json,
    '🏙️ Exclusive penthouse with 360-degree views of Burj Khalifa and Dubai Fountain. Ultimate luxury living in the heart of Downtown Dubai.',
    9.0,
    7.5,
    true,
    '[
        "https://images.unsplash.com/photo-1600585154084-4e5fe7c39198?w=1200",
        "https://images.unsplash.com/photo-1600566752355-35792bedcfea?w=1200",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200",
        "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1200"
    ]'::json,
    'https://images.unsplash.com/photo-1600585154084-4e5fe7c39198?w=1200',
    true,
    true,
    false,
    NOW(),
    NOW()
);

-- 6. ملک اداری Business Bay (Commercial)
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    image_urls, primary_image,
    is_available, is_featured, is_urgent,
    created_at, updated_at
) VALUES (
    2,
    'Business Bay Office Space',
    'COMMERCIAL',
    'BUY',
    'Business Bay',
    'Business Bay Towers, Dubai, UAE',
    1200000.0,
    600.0,
    'AED',
    0,
    2,
    2000.0,
    '["Fitted Office", "Meeting Rooms", "Parking", "Reception Area", "Pantry", "High-Speed Internet"]'::json,
    '🏢 Prime office space in Business Bay with fitted interiors. Perfect for businesses seeking prestigious Dubai address with excellent ROI.',
    11.0,
    9.5,
    false,
    '[
        "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1200",
        "https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=1200",
        "https://images.unsplash.com/photo-1497366412874-3415097a27e7?w=1200"
    ]'::json,
    'https://images.unsplash.com/photo-1497366216548-37526070297c?w=1200',
    true,
    false,
    false,
    NOW(),
    NOW()
);

-- چک کردن نتیجه
SELECT 
    id, name, property_type, location, price, bedrooms,
    golden_visa_eligible, is_featured, is_urgent
FROM tenant_properties 
WHERE tenant_id = 2
ORDER BY created_at DESC;
