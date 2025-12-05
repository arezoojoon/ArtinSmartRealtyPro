"""add admin_chat_id and ghost_reminder_sent columns

Revision ID: 001_sales_features
Revises: 
Create Date: 2025-12-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_sales_features'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add columns for high-velocity sales features."""
    # Add admin_chat_id to tenants table
    op.add_column('tenants', 
        sa.Column('admin_chat_id', sa.String(length=255), nullable=True)
    )
    
    # Add ghost_reminder_sent to leads table
    op.add_column('leads', 
        sa.Column('ghost_reminder_sent', sa.Boolean(), server_default=sa.text('false'), nullable=True)
    )


def downgrade() -> None:
    """Remove sales feature columns."""
    op.drop_column('leads', 'ghost_reminder_sent')
    op.drop_column('tenants', 'admin_chat_id')
