"""
Initialize database schema
"""

import asyncio
from database import engine, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """Create all tables."""
    logger.info("🔧 Creating database tables...")
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Database tables created successfully!")
    
    logger.info("✨ Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())
