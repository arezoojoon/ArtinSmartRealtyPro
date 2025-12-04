import asyncio
import sys
sys.path.insert(0, 'backend')

from database import async_session, TenantProperty
from sqlalchemy import select

async def check_properties():
    async with async_session() as db:
        result = await db.execute(
            select(TenantProperty)
            .where(TenantProperty.tenant_id == 1)
            .limit(5)
        )
        props = result.scalars().all()
        
        if not props:
            print("❌ No properties found in database!")
            return
        
        print(f"Found {len(props)} properties:\n")
        for p in props:
            print(f"📍 {p.name}")
            print(f"   Price: {p.price} {p.currency}")
            print(f"   ROI: {p.expected_roi}%")
            print(f"   Rental Yield: {p.rental_yield}%")
            print(f"   Mortgage Available: {p.golden_visa_eligible}")
            print()

if __name__ == "__main__":
    asyncio.run(check_properties())
