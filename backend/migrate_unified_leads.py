"""
Database Migration: Create Unified Lead System
Adds new tables for unified lead management and follow-up campaigns
"""

import asyncio
from sqlalchemy import text
from backend.database import engine, async_session
from backend.unified_database import Base, UnifiedLead, LeadInteraction, FollowupCampaign, PropertyLeadMatch


async def create_unified_tables():
    """Create all unified lead system tables"""
    print("🚀 Creating Unified Lead System Tables...")
    
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Tables created successfully!")
    
    # Verify tables exist
    async with async_session() as session:
        # Check unified_leads table
        result = await session.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'unified_leads'
        """))
        count = result.scalar()
        print(f"   - unified_leads: {'✅' if count > 0 else '❌'}")
        
        # Check lead_interactions table
        result = await session.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'lead_interactions'
        """))
        count = result.scalar()
        print(f"   - lead_interactions: {'✅' if count > 0 else '❌'}")
        
        # Check followup_campaigns table
        result = await session.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'followup_campaigns'
        """))
        count = result.scalar()
        print(f"   - followup_campaigns: {'✅' if count > 0 else '❌'}")
        
        # Check property_lead_matches table
        result = await session.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'property_lead_matches'
        """))
        count = result.scalar()
        print(f"   - property_lead_matches: {'✅' if count > 0 else '❌'}")


async def migrate_linkedin_leads():
    """
    Migrate existing leads from LinkedIn Scraper SQLite database
    to unified_leads table in PostgreSQL
    """
    print("\n📦 Migrating LinkedIn Scraper Leads...")
    
    import sqlite3
    from pathlib import Path
    
    # Path to LinkedIn scraper database
    linkedin_db_path = Path("i:/real state salesman/AI Lead Scraper & Personalize/backend/leads_database.db")
    
    if not linkedin_db_path.exists():
        print(f"   ⚠️  LinkedIn database not found at: {linkedin_db_path}")
        return
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(linkedin_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    # Get all leads from SQLite
    cursor.execute("SELECT * FROM leads")
    sqlite_leads = cursor.fetchall()
    
    print(f"   Found {len(sqlite_leads)} LinkedIn leads")
    
    # Migrate to PostgreSQL
    async with async_session() as session:
        migrated = 0
        skipped = 0
        
        for row in sqlite_leads:
            # Parse experience and posts from JSON strings
            import json
            experience = json.loads(row['experience_json']) if row['experience_json'] else None
            posts = json.loads(row['recent_posts_json']) if row['recent_posts_json'] else None
            
            # Create unified lead
            lead_data = {
                'name': row['name'],
                'email': row['email'],
                'phone': row['phone'],
                'linkedin_url': row['linkedin_url'],
                'job_title': row['job_title'],
                'company': row['company'],
                'about': row['about'],
                'location': row['location'],
                'linkedin_experience': experience,
                'linkedin_posts': posts,
                'source': 'linkedin',
                'status': 'new',
                'tenant_id': 1,  # Assign to default tenant (you can change this)
            }
            
            try:
                # Use find_or_create_lead to avoid duplicates
                from backend.unified_database import find_or_create_lead
                lead, created = await find_or_create_lead(session, tenant_id=1, data=lead_data)
                
                if created:
                    migrated += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"   ⚠️  Error migrating lead {row['name']}: {e}")
                continue
        
        await session.commit()
    
    sqlite_conn.close()
    
    print(f"   ✅ Migrated: {migrated} leads")
    print(f"   ⏭️  Skipped (duplicates): {skipped} leads")


async def migrate_bot_leads():
    """
    Migrate existing leads from ArtinSmartRealty bot (from 'leads' table)
    to unified_leads table
    """
    print("\n📦 Migrating Bot Leads...")
    
    async with async_session() as session:
        # Check if 'leads' table exists
        result = await session.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'leads'
        """))
        count = result.scalar()
        
        if count == 0:
            print("   ⚠️  'leads' table not found. Skipping migration.")
            return
        
        # Get all existing bot leads
        result = await session.execute(text("SELECT * FROM leads"))
        bot_leads = result.fetchall()
        
        print(f"   Found {len(bot_leads)} bot leads")
        
        migrated = 0
        skipped = 0
        
        for row in bot_leads:
            lead_data = {
                'name': row.name,
                'phone': row.phone,
                'telegram_user_id': row.telegram_user_id if hasattr(row, 'telegram_user_id') else None,
                'whatsapp_number': row.whatsapp_number if hasattr(row, 'whatsapp_number') else None,
                'language': row.language if hasattr(row, 'language') else 'en',
                'transaction_type': row.transaction_type if hasattr(row, 'transaction_type') else None,
                'property_type': row.property_type if hasattr(row, 'property_type') else None,
                'budget_min': row.budget_min if hasattr(row, 'budget_min') else None,
                'budget_max': row.budget_max if hasattr(row, 'budget_max') else None,
                'bedrooms': row.bedrooms if hasattr(row, 'bedrooms') else None,
                'purpose': row.purpose if hasattr(row, 'purpose') else None,
                'payment_method': row.payment_method if hasattr(row, 'payment_method') else None,
                'source': 'telegram' if hasattr(row, 'telegram_user_id') and row.telegram_user_id else 'whatsapp',
                'status': 'qualified' if hasattr(row, 'budget_min') and row.budget_min else 'new',
                'tenant_id': row.tenant_id if hasattr(row, 'tenant_id') else 1,
                'conversation_state': row.state if hasattr(row, 'state') else None,
            }
            
            try:
                from backend.unified_database import find_or_create_lead
                lead, created = await find_or_create_lead(
                    session, 
                    tenant_id=lead_data['tenant_id'], 
                    data=lead_data
                )
                
                if created:
                    migrated += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"   ⚠️  Error migrating lead {row.name}: {e}")
                continue
        
        await session.commit()
    
    print(f"   ✅ Migrated: {migrated} leads")
    print(f"   ⏭️  Skipped (duplicates): {skipped} leads")


async def add_tenant_relationships():
    """
    Add relationship fields to Tenant model for unified_leads and followup_campaigns
    """
    print("\n🔗 Adding Tenant Relationships...")
    
    # Note: This should be done by updating the Tenant model in database.py
    # For now, we'll just verify the foreign keys exist
    
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT COUNT(*) FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY' 
            AND table_name = 'unified_leads'
            AND constraint_name LIKE '%tenant%'
        """))
        count = result.scalar()
        print(f"   - unified_leads -> tenants FK: {'✅' if count > 0 else '❌'}")
        
        result = await session.execute(text("""
            SELECT COUNT(*) FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY' 
            AND table_name = 'followup_campaigns'
            AND constraint_name LIKE '%tenant%'
        """))
        count = result.scalar()
        print(f"   - followup_campaigns -> tenants FK: {'✅' if count > 0 else '❌'}")


async def main():
    """Run all migrations"""
    print("=" * 60)
    print("  UNIFIED LEAD SYSTEM MIGRATION")
    print("=" * 60)
    
    try:
        # Step 1: Create new tables
        await create_unified_tables()
        
        # Step 2: Migrate LinkedIn leads
        await migrate_linkedin_leads()
        
        # Step 3: Migrate bot leads
        await migrate_bot_leads()
        
        # Step 4: Verify relationships
        await add_tenant_relationships()
        
        print("\n" + "=" * 60)
        print("  ✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
