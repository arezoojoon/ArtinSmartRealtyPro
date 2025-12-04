#!/usr/bin/env python3
"""
Test script to check production data status
Run this on the production server to verify:
1. Properties have ROI/Rental Yield data
2. Active lotteries exist
"""
import asyncio
import sys
sys.path.insert(0, '/opt/ArtinSmartRealty/backend')

from database import async_session, TenantProperty, Tenant
from sqlalchemy import select
from api.lotteries import LOTTERIES_DB
from datetime import datetime


async def main():
    print("=" * 60)
    print("🔍 PRODUCTION DATA STATUS CHECK")
    print("=" * 60)
    print()
    
    # Check properties with ROI data
    async with async_session() as db:
        # Get all tenants
        result = await db.execute(select(Tenant))
        tenants = result.scalars().all()
        
        for tenant in tenants:
            print(f"📊 Tenant: {tenant.name} (ID: {tenant.id})")
            print("-" * 60)
            
            # Get properties for this tenant
            prop_result = await db.execute(
                select(TenantProperty)
                .where(TenantProperty.tenant_id == tenant.id)
                .where(TenantProperty.is_available == True)
            )
            properties = prop_result.scalars().all()
            
            if not properties:
                print("   ❌ No properties found!")
            else:
                print(f"   ✅ Found {len(properties)} properties\n")
                
                roi_count = 0
                yield_count = 0
                
                for p in properties:
                    print(f"   🏠 {p.name}")
                    print(f"      Price: {p.price:,.0f} {p.currency}")
                    print(f"      Type: {p.property_type}")
                    
                    if p.expected_roi:
                        print(f"      ✅ ROI: {p.expected_roi}%")
                        roi_count += 1
                    else:
                        print(f"      ❌ ROI: Not set")
                    
                    if p.rental_yield:
                        print(f"      ✅ Rental Yield: {p.rental_yield}%")
                        yield_count += 1
                    else:
                        print(f"      ❌ Rental Yield: Not set")
                    
                    print()
                
                print(f"   📈 Summary: {roi_count}/{len(properties)} have ROI, {yield_count}/{len(properties)} have Rental Yield")
            
            print()
    
    # Check lotteries
    print("=" * 60)
    print("🎁 LOTTERY STATUS")
    print("=" * 60)
    print()
    
    if not LOTTERIES_DB:
        print("❌ No lotteries in system (LOTTERIES_DB is empty)")
        print()
        print("💡 To create a lottery:")
        print("   1. Go to dashboard")
        print("   2. Navigate to Settings → Lotteries")
        print("   3. Click 'Create New Lottery'")
        print("   4. Set prize, dates, and activate")
    else:
        print(f"✅ Found {len(LOTTERIES_DB)} lottery/lotteries\n")
        
        for lottery_id, lottery in LOTTERIES_DB.items():
            status_emoji = "🟢" if lottery['status'] == 'active' else "🔴"
            print(f"{status_emoji} Lottery #{lottery_id}: {lottery['name']}")
            print(f"   Prize: {lottery['prize']}")
            print(f"   Status: {lottery['status']}")
            print(f"   Start: {lottery['start_date']}")
            print(f"   End: {lottery['end_date']}")
            print(f"   Participants: {len(lottery.get('participants', []))}")
            
            # Check if active and not expired
            now = datetime.utcnow()
            if lottery['status'] == 'active' and lottery['end_date'] > now:
                print(f"   ✅ ACTIVE - Will show in bot!")
            elif lottery['end_date'] <= now:
                print(f"   ⏰ EXPIRED - Won't show in bot")
            else:
                print(f"   ⏸️  PAUSED - Won't show in bot")
            
            print()
    
    print("=" * 60)
    print("✅ CHECK COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
