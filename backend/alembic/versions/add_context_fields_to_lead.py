"""add context fields to lead

Revision ID: 003_context_fields
Revises: 002_subscription_status
Create Date: 2025-11-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_context_fields'
down_revision = '002_subscription_status'
branch_labels = None
depends_on = None


def upgrade():
    """Add filled_slots and pending_slot columns to Lead table."""
    # Add filled_slots column (JSONB for tracking which slots are completed)
    op.add_column('lead', 
        sa.Column('filled_slots', postgresql.JSONB, nullable=True, server_default='{}')
    )
    
    # Add pending_slot column (VARCHAR for tracking current slot being filled)
    op.add_column('lead',
        sa.Column('pending_slot', sa.String(length=50), nullable=True)
    )
    
    print("✅ Migration UP: filled_slots and pending_slot added to Lead table")


def downgrade():
    """Remove filled_slots and pending_slot columns."""
    op.drop_column('lead', 'pending_slot')
    op.drop_column('lead', 'filled_slots')
    
    print("✅ Migration DOWN: filled_slots and pending_slot removed from Lead table")
