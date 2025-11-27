"""
Setup Sample Data for ArtinSmartRealty
This script adds sample properties, projects, and knowledge base entries
Run this after deploying to populate tenant data
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import (
    async_session, Tenant, TenantProperty, TenantProject, TenantKnowledge,
    PropertyType, TransactionType, Language, init_db
)
from sqlalchemy.future import select


async def add_sample_properties(tenant_id: int):
    """Add sample properties for a tenant."""
    
    sample_properties = [
        {
            "name": "Luxury Marina Apartment",
            "property_type": PropertyType.APARTMENT,
            "transaction_type": TransactionType.BUY,
            "location": "Dubai Marina",
            "address": "Marina Tower, Dubai Marina",
            "price": 1500000,
            "price_per_sqft": 1500,
            "currency": "AED",
            "bedrooms": 2,
            "bathrooms": 2,
            "area_sqft": 1000,
            "features": ["Sea View", "Balcony", "Parking", "Gym", "Pool"],
            "description": "Stunning 2-bedroom apartment with breathtaking marina views. Modern finishes and world-class amenities.",
            "expected_roi": 8.5,
            "rental_yield": 7.2,
            "golden_visa_eligible": True,
            "images": ["https://example.com/image1.jpg"],
            "is_featured": True,
            "is_available": True
        },
        {
            "name": "Downtown Penthouse",
            "property_type": PropertyType.PENTHOUSE,
            "transaction_type": TransactionType.BUY,
            "location": "Downtown Dubai",
            "address": "Burj Khalifa District",
            "price": 5000000,
            "price_per_sqft": 2500,
            "currency": "AED",
            "bedrooms": 4,
            "bathrooms": 5,
            "area_sqft": 2000,
            "features": ["Burj Khalifa View", "Private Pool", "Terrace", "Smart Home", "Concierge"],
            "description": "Ultra-luxury penthouse in the heart of Downtown Dubai with panoramic city views.",
            "expected_roi": 12.0,
            "rental_yield": 6.5,
            "golden_visa_eligible": True,
            "images": ["https://example.com/image2.jpg"],
            "is_featured": True,
            "is_available": True
        },
        {
            "name": "Arabian Ranches Villa",
            "property_type": PropertyType.VILLA,
            "transaction_type": TransactionType.BUY,
            "location": "Arabian Ranches",
            "address": "Arabian Ranches 3",
            "price": 3200000,
            "price_per_sqft": 800,
            "currency": "AED",
            "bedrooms": 5,
            "bathrooms": 6,
            "area_sqft": 4000,
            "features": ["Private Garden", "Maid's Room", "Golf Course View", "Gated Community"],
            "description": "Spacious family villa in prestigious Arabian Ranches community.",
            "expected_roi": 9.0,
            "rental_yield": 5.8,
            "golden_visa_eligible": True,
            "images": ["https://example.com/image3.jpg"],
            "is_featured": False,
            "is_available": True
        },
        {
            "name": "Business Bay Studio",
            "property_type": PropertyType.APARTMENT,
            "transaction_type": TransactionType.BUY,
            "location": "Business Bay",
            "address": "Executive Towers, Business Bay",
            "price": 650000,
            "price_per_sqft": 1300,
            "currency": "AED",
            "bedrooms": 0,
            "bathrooms": 1,
            "area_sqft": 500,
            "features": ["City View", "Fully Furnished", "High ROI"],
            "description": "Perfect investment opportunity with high rental yield in Business Bay.",
            "expected_roi": 10.5,
            "rental_yield": 8.5,
            "golden_visa_eligible": False,
            "images": ["https://example.com/image4.jpg"],
            "is_featured": False,
            "is_available": True
        }
    ]
    
    async with async_session() as session:
        for prop_data in sample_properties:
            prop = TenantProperty(tenant_id=tenant_id, **prop_data)
            session.add(prop)
        
        await session.commit()
        print(f"✅ Added {len(sample_properties)} sample properties")


async def add_sample_projects(tenant_id: int):
    """Add sample off-plan projects for a tenant."""
    
    sample_projects = [
        {
            "name": "Emaar Beachfront Residences",
            "developer": "Emaar Properties",
            "location": "Dubai Harbour",
            "starting_price": 2500000,
            "price_per_sqft": 2000,
            "currency": "AED",
            "payment_plan": "60/40 (60% during construction, 40% on handover)",
            "down_payment_percent": 20,
            "handover_date": datetime(2026, 12, 31),
            "completion_percent": 45,
            "projected_roi": 25.0,
            "projected_rental_yield": 7.5,
            "golden_visa_eligible": True,
            "amenities": ["Private Beach", "Marina", "Retail", "Restaurants", "Kids Play Area"],
            "unit_types": ["Studio", "1BR", "2BR", "3BR"],
            "description": "Exclusive beachfront living with stunning sea views and world-class amenities.",
            "selling_points": [
                "Prime beachfront location",
                "Flexible payment plan",
                "High appreciation potential",
                "Golden Visa eligible"
            ],
            "is_featured": True,
            "is_active": True
        },
        {
            "name": "Sobha Hartland 2",
            "developer": "Sobha Realty",
            "location": "Mohammed Bin Rashid City",
            "starting_price": 1200000,
            "price_per_sqft": 1500,
            "currency": "AED",
            "payment_plan": "70/30 (70% during construction, 30% on handover)",
            "down_payment_percent": 10,
            "handover_date": datetime(2027, 6, 30),
            "completion_percent": 30,
            "projected_roi": 30.0,
            "projected_rental_yield": 8.0,
            "golden_visa_eligible": True,
            "amenities": ["Lagoon", "Beach", "Parks", "Schools", "Mosques"],
            "unit_types": ["1BR", "2BR", "3BR", "4BR", "Villas"],
            "description": "Award-winning waterfront community with lush green spaces and crystal lagoons.",
            "selling_points": [
                "Eco-friendly design",
                "10% down payment only",
                "Expected 30% ROI",
                "Family-oriented community"
            ],
            "is_featured": True,
            "is_active": True
        }
    ]
    
    async with async_session() as session:
        for proj_data in sample_projects:
            project = TenantProject(tenant_id=tenant_id, **proj_data)
            session.add(project)
        
        await session.commit()
        print(f"✅ Added {len(sample_projects)} sample projects")


async def add_sample_knowledge(tenant_id: int):
    """Add sample knowledge base entries."""
    
    sample_knowledge = [
        {
            "category": "faq",
            "title": "What is Golden Visa?",
            "content": "The UAE Golden Visa is a long-term residency visa that allows foreign investors and professionals to live, work, and study in the UAE without the need for a national sponsor. Properties valued at AED 2 million or more qualify for this 10-year visa.",
            "language": Language.EN,
            "keywords": ["golden visa", "residency", "long-term", "investment"],
            "priority": 100,
            "is_active": True
        },
        {
            "category": "faq",
            "title": "ویزای طلایی چیست؟",
            "content": "ویزای طلایی امارات یک ویزای اقامت بلندمدت است که به سرمایه‌گذاران و متخصصان خارجی اجازه می‌دهد بدون نیاز به اسپانسر ملی در امارات زندگی، کار و تحصیل کنند. املاکی با ارزش 2 میلیون درهم یا بیشتر واجد شرایط این ویزای 10 ساله هستند.",
            "language": Language.FA,
            "keywords": ["ویزا طلایی", "اقامت", "سرمایه‌گذاری"],
            "priority": 100,
            "is_active": True
        },
        {
            "category": "service",
            "title": "Our Services",
            "content": "We provide comprehensive real estate services including property search, investment consulting, legal assistance, mortgage arrangement, and after-sales support. Our team ensures a smooth buying experience from start to finish.",
            "language": Language.EN,
            "keywords": ["services", "support", "consulting"],
            "priority": 80,
            "is_active": True
        },
        {
            "category": "policy",
            "title": "Payment Terms",
            "content": "We offer flexible payment plans including cash purchases, developer payment plans (typically 60/40 or 70/30), and mortgage assistance with local banks. Down payment requirements vary from 10% to 25% depending on the property type.",
            "language": Language.EN,
            "keywords": ["payment", "mortgage", "financing"],
            "priority": 70,
            "is_active": True
        }
    ]
    
    async with async_session() as session:
        for kb_data in sample_knowledge:
            knowledge = TenantKnowledge(tenant_id=tenant_id, **kb_data)
            session.add(knowledge)
        
        await session.commit()
        print(f"✅ Added {len(sample_knowledge)} knowledge base entries")


async def get_tenant_by_email(email: str) -> int:
    """Get tenant ID by email."""
    async with async_session() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.email == email)
        )
        tenant = result.scalar_one_or_none()
        
        if tenant:
            return tenant.id
        else:
            return None


async def main():
    """Main setup function."""
    print("=" * 60)
    print("ArtinSmartRealty - Sample Data Setup")
    print("=" * 60)
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Get tenant email from user
    tenant_email = input("\nEnter your tenant email (or press Enter for all tenants): ").strip()
    
    if tenant_email:
        tenant_id = await get_tenant_by_email(tenant_email)
        if not tenant_id:
            print(f"❌ Tenant with email '{tenant_email}' not found!")
            return
        
        tenant_ids = [tenant_id]
    else:
        # Get all active tenants
        async with async_session() as session:
            result = await session.execute(
                select(Tenant).where(Tenant.is_active == True)
            )
            tenants = result.scalars().all()
            tenant_ids = [t.id for t in tenants]
            
            if not tenant_ids:
                print("❌ No active tenants found!")
                return
    
    # Add sample data for each tenant
    for tenant_id in tenant_ids:
        print(f"\n📦 Adding sample data for Tenant ID: {tenant_id}")
        
        # Get tenant name
        async with async_session() as session:
            result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one_or_none()
            print(f"   Agent: {tenant.name}")
        
        await add_sample_properties(tenant_id)
        await add_sample_projects(tenant_id)
        await add_sample_knowledge(tenant_id)
    
    print("\n" + "=" * 60)
    print("✅ Sample data setup complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Login to https://realty.artinsmartagent.com")
    print("2. Test the Telegram bot - it will show properties")
    print("3. Manage properties from the dashboard")


if __name__ == "__main__":
    asyncio.run(main())
