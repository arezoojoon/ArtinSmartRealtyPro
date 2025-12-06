"""Add brochure_pdf field to tenant_properties

Revision ID: add_brochure_pdf
Revises: 
Create Date: 2024-12-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_brochure_pdf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add brochure_pdf column to tenant_properties table
    op.add_column('tenant_properties', sa.Column('brochure_pdf', sa.String(512), nullable=True))


def downgrade():
    # Remove brochure_pdf column
    op.drop_column('tenant_properties', 'brochure_pdf')
