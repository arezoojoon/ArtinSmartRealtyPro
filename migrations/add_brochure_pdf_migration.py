"""
Add brochure_pdf field to tenant_properties table
Run this script to migrate the database
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import engine
from sqlalchemy import text

async def run_migration():
    """Add brochure_pdf column to tenant_properties"""
    async with engine.begin() as conn:
        # Check if column exists
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='tenant_properties' AND column_name='brochure_pdf';
        """
        result = await conn.execute(text(check_query))
        exists = result.fetchone() is not None
        
        if exists:
            print("✅ Column 'brochure_pdf' already exists in tenant_properties table")
            return
        
        # Add column
        alter_query = """
        ALTER TABLE tenant_properties 
        ADD COLUMN brochure_pdf VARCHAR(512);
        """
        await conn.execute(text(alter_query))
        print("✅ Successfully added 'brochure_pdf' column to tenant_properties table")

if __name__ == "__main__":
    print("🔄 Running migration: Add brochure_pdf to tenant_properties...")
    asyncio.run(run_migration())
    print("✅ Migration completed successfully!")
