"""
Database Migration: Add Lead Scoring & Engagement Tracking
Adds columns for sales intelligence system
Run: python backend/migrate_add_lead_scoring.py
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine, async_session


async def migrate():
    """Add lead scoring columns to leads table."""
    
    print("🔄 Starting migration: Add lead scoring columns...")
    
    async with engine.begin() as conn:
        # Check if columns already exist
        check_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='leads' AND column_name='lead_score';
        """
        result = await conn.execute(text(check_sql))
        exists = result.fetchone()
        
        if exists:
            print("✅ Columns already exist. Skipping migration.")
            return
        
        # Add new columns
        migrations = [
            """
            ALTER TABLE leads 
            ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 0;
            """,
            """
            ALTER TABLE leads 
            ADD COLUMN IF NOT EXISTS temperature VARCHAR(20) DEFAULT 'cold';
            """,
            """
            ALTER TABLE leads 
            ADD COLUMN IF NOT EXISTS qr_scan_count INTEGER DEFAULT 0;
            """,
            """
            ALTER TABLE leads 
            ADD COLUMN IF NOT EXISTS catalog_views INTEGER DEFAULT 0;
            """,
            """
            ALTER TABLE leads 
            ADD COLUMN IF NOT EXISTS messages_count INTEGER DEFAULT 0;
            """,
            """
            ALTER TABLE leads 
            ADD COLUMN IF NOT EXISTS total_interactions INTEGER DEFAULT 0;
            """,
        ]
        
        for sql in migrations:
            print(f"  Executing: {sql.strip()[:60]}...")
            await conn.execute(text(sql))
        
        # Create index on lead_score for fast sorting
        index_sql = """
        CREATE INDEX IF NOT EXISTS idx_leads_score 
        ON leads(lead_score DESC);
        """
        print(f"  Creating index on lead_score...")
        await conn.execute(text(index_sql))
        
        print("✅ Migration completed successfully!")
        print("\n📊 New columns added:")
        print("  - lead_score (INTEGER, 0-100)")
        print("  - temperature (VARCHAR, 'burning'/'hot'/'warm'/'cold')")
        print("  - qr_scan_count (INTEGER)")
        print("  - catalog_views (INTEGER)")
        print("  - messages_count (INTEGER)")
        print("  - total_interactions (INTEGER)")
        print("\n🎯 Next steps:")
        print("  1. Restart backend: docker-compose restart backend")
        print("  2. Verify in dashboard: Check lead cards show scoring")
        print("  3. Test scoring: Send messages to bot and watch score increase")


async def backfill_existing_leads():
    """
    Backfill scores for existing leads based on their current data.
    Optional: Run after migration to score existing leads.
    """
    from lead_scoring import update_lead_score
    from database import Lead
    from sqlalchemy.future import select
    
    print("\n🔄 Backfilling scores for existing leads...")
    
    async with async_session() as session:
        result = await session.execute(select(Lead))
        leads = result.scalars().all()
        
        count = 0
        for lead in leads:
            # Count existing interactions from conversation history
            # (This is approximate - real tracking starts after migration)
            if lead.voice_transcript:
                lead.messages_count = 1
            
            update_lead_score(lead)
            count += 1
        
        await session.commit()
        print(f"✅ Backfilled scores for {count} leads")
        
        # Show sample
        result = await session.execute(
            select(Lead).order_by(Lead.lead_score.desc()).limit(5)
        )
        top_leads = result.scalars().all()
        
        print("\n🔥 Top 5 Hottest Leads:")
        for lead in top_leads:
            print(f"  {lead.name or 'Anonymous'}: {lead.lead_score} ({lead.temperature})")


if __name__ == "__main__":
    print("=" * 60)
    print("LEAD SCORING MIGRATION")
    print("=" * 60)
    
    # Run migration
    asyncio.run(migrate())
    
    # Ask if user wants to backfill
    response = input("\n⚠️  Backfill scores for existing leads? (y/N): ")
    if response.lower() == 'y':
        asyncio.run(backfill_existing_leads())
    else:
        print("⏭️  Skipped backfill. New leads will be scored automatically.")
    
    print("\n✅ All done! Your sales intelligence system is ready.")
