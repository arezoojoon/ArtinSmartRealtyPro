"""
Database Migration: Add Subscription Plans
Adds SubscriptionPlan enum and updates Tenant table
"""

import asyncio
from sqlalchemy import text
from backend.database import engine, async_session


async def migrate_subscription_plans():
    """Add subscription plan columns to tenants table"""
    
    print("🚀 Starting Subscription Plan Migration...")
    
    async with engine.begin() as conn:
        # Step 1: Create SubscriptionPlan enum type
        print("\n📦 Creating SubscriptionPlan enum...")
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE subscriptionplan AS ENUM ('free', 'basic', 'pro');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        print("   ✅ SubscriptionPlan enum created")
        
        # Step 2: Update SubscriptionStatus enum (add 'expired')
        print("\n📦 Updating SubscriptionStatus enum...")
        await conn.execute(text("""
            ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'expired';
        """))
        print("   ✅ SubscriptionStatus enum updated")
        
        # Step 3: Add new columns to tenants table
        print("\n📦 Adding subscription columns to tenants table...")
        
        columns_to_add = [
            ("subscription_plan", "subscriptionplan DEFAULT 'free'"),
            ("subscription_starts_at", "TIMESTAMP"),
            ("subscription_ends_at", "TIMESTAMP"),
            ("billing_cycle", "VARCHAR(20) DEFAULT 'monthly'"),
            ("payment_method", "VARCHAR(50)"),
            ("last_payment_date", "TIMESTAMP"),
            ("next_payment_date", "TIMESTAMP"),
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(text(f"""
                    ALTER TABLE tenants 
                    ADD COLUMN IF NOT EXISTS {column_name} {column_type};
                """))
                print(f"   ✅ Added column: {column_name}")
            except Exception as e:
                print(f"   ⚠️  Column {column_name} already exists or error: {e}")
        
        # Step 4: Update existing tenants to have 'free' plan
        print("\n📦 Migrating existing tenants...")
        await conn.execute(text("""
            UPDATE tenants 
            SET subscription_plan = 'free' 
            WHERE subscription_plan IS NULL;
        """))
        print("   ✅ Existing tenants migrated to free plan")
        
    print("\n✅ Migration completed successfully!")
    print("\n📊 Summary:")
    print("   - SubscriptionPlan enum: free, basic, pro")
    print("   - SubscriptionStatus enum: trial, active, suspended, cancelled, expired")
    print("   - New columns: subscription_plan, subscription_starts_at, subscription_ends_at,")
    print("                  billing_cycle, payment_method, last_payment_date, next_payment_date")


async def verify_migration():
    """Verify migration was successful"""
    print("\n🔍 Verifying migration...")
    
    async with async_session() as session:
        # Count tenants
        result = await session.execute(text("SELECT COUNT(*) FROM tenants"))
        count = result.scalar()
        print(f"   ✅ Total tenants: {count}")
        
        # Check columns exist
        result = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tenants' 
            AND column_name IN ('subscription_plan', 'billing_cycle', 'subscription_starts_at');
        """))
        columns = [row[0] for row in result.fetchall()]
        print(f"   ✅ New columns found: {', '.join(columns)}")
    
    print("\n✅ Verification complete!")


async def main():
    try:
        await migrate_subscription_plans()
        await verify_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
