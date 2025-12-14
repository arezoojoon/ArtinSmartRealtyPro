-- 🏠 اضافه کردن املاک نمونه برای تست بات
-- این املاک برای tenant_id=1 اضافه میشن

-- اول چک کنیم ببینیم قبلاً املاکی اضافه شده یا نه
SELECT COUNT(*) as current_count FROM tenant_properties WHERE tenant_id = 1;

-- اگه خالی بود، این املاک رو اضافه می‌کنیم

-- 1. آپارتمان لوکس دبی مارینا (مناسب ویزای طلایی)
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    primary_image, is_available, is_featured, is_urgent,
    created_at, updated_at
) VALUES (
    1, 
    'Marina Heights Luxury Tower', 
    'APARTMENT', 
    'BUY',
    'Dubai Marina', 
    'Dubai Marina, Dubai, UAE',
    2500000.0, 
    2000.0, 
    'AED',
    3, 
    3, 
    1250.0,
    '["Sea View", "High Floor", "Gym & Pool", "Covered Parking", "24/7 Security", "Smart Home"]'::json,
    '🌊 3-bedroom luxury apartment with stunning sea views in the heart of Dubai Marina. Features modern finishes, spacious balcony, and access to world-class amenities.',
    8.5, 
    7.2,
    true,
    'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800',
    true, 
    true, 
    false,
    NOW(), 
    NOW()
) ON CONFLICT DO NOTHING;

-- 2. استودیو برای سرمایه‌گذاری
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    primary_image, is_available, is_featured,
    created_at, updated_at
) VALUES (
    1,
    'Investment Studio - Downtown',
    'STUDIO',
    'BUY',
    'Downtown Dubai',
    'Downtown Dubai, UAE',
    850000.0,
    1700.0,
    'AED',
    0,
    1,
    500.0,
    '["Furnished", "Pool Access", "Close to Metro", "High ROI"]'::json,
    '💰 Perfect investment opportunity! Fully furnished studio in Downtown with guaranteed 9% annual ROI. Ideal for Airbnb or long-term rental.',
    9.2,
    8.5,
    false,
    'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800',
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 3. ویلا دوبلکس با استخر
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    primary_image, is_available, is_featured,
    created_at, updated_at
) VALUES (
    1,
    'Luxury Villa with Private Pool',
    'VILLA',
    'BUY',
    'Arabian Ranches',
    'Arabian Ranches, Dubai, UAE',
    4200000.0,
    1500.0,
    'AED',
    5,
    6,
    2800.0,
    '["Private Pool", "Garden", "Maid Room", "Study Room", "Smart Home", "Golf Course View"]'::json,
    '🏡 Stunning 5-bedroom villa with private pool and garden. Perfect for families seeking luxury lifestyle in a gated community with golf course access.',
    6.5,
    5.8,
    true,
    'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800',
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 4. آپارتمان پیش‌فروش (off-plan)
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    primary_image, is_available, is_featured, is_urgent,
    created_at, updated_at
) VALUES (
    1,
    'Sky Gardens - Off-Plan',
    'APARTMENT',
    'BUY',
    'Business Bay',
    'Business Bay, Dubai, UAE',
    1200000.0,
    1900.0,
    'AED',
    2,
    2,
    630.0,
    '["Off-Plan", "Payment Plan 60/40", "Burj Khalifa View", "Gym", "Rooftop Pool"]'::json,
    '🏗️ Pre-construction opportunity! 2BR apartment with flexible payment plan (20% down, 40% during construction, 40% on handover). Expected completion: Q4 2025. High ROI potential!',
    10.5,
    9.0,
    false,
    'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800',
    true,
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- 5. پنت‌هاوس لوکس
INSERT INTO tenant_properties (
    tenant_id, name, property_type, transaction_type,
    location, address,
    price, price_per_sqft, currency,
    bedrooms, bathrooms, area_sqft,
    features, description,
    expected_roi, rental_yield,
    golden_visa_eligible,
    primary_image, is_available, is_featured,
    created_at, updated_at
) VALUES (
    1,
    'Exclusive Penthouse - Palm Jumeirah',
    'PENTHOUSE',
    'BUY',
    'Palm Jumeirah',
    'Palm Jumeirah, Dubai, UAE',
    8500000.0,
    3000.0,
    'AED',
    4,
    5,
    2833.0,
    '["Private Elevator", "360° View", "Jacuzzi", "Beach Access", "Concierge Service", "Wine Cellar"]'::json,
    '👑 Ultra-luxury penthouse on the iconic Palm Jumeirah. Features private rooftop terrace, panoramic sea views, and exclusive beach access. For discerning buyers only.',
    5.5,
    4.8,
    true,
    'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800',
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- چک کردن اینکه چند تا ملک اضافه شده
SELECT 
    COUNT(*) as total_properties,
    SUM(CASE WHEN golden_visa_eligible = true THEN 1 ELSE 0 END) as golden_visa_count,
    SUM(CASE WHEN is_featured = true THEN 1 ELSE 0 END) as featured_count
FROM tenant_properties 
WHERE tenant_id = 1;

-- نمایش املاک اضافه شده
SELECT 
    id,
    name,
    property_type,
    location,
    price,
    bedrooms,
    expected_roi,
    golden_visa_eligible,
    is_featured
FROM tenant_properties 
WHERE tenant_id = 1
ORDER BY is_featured DESC, price ASC;

-- ✅ تمام! حالا بات می‌تونه این املاک رو نشون بده
