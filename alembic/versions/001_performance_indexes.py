"""
Database Performance Optimization Migration
Adds indexes for faster queries
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes"""
    
    # === UNIFIED_LEADS TABLE ===
    
    # Index for tenant isolation (most common filter)
    op.create_index(
        'idx_leads_tenant_id',
        'unified_leads',
        ['tenant_id'],
        unique=False
    )
    
    # Index for status + tenant (common dashboard query)
    op.create_index(
        'idx_leads_tenant_status',
        'unified_leads',
        ['tenant_id', 'status'],
        unique=False
    )
    
    # Index for grade + tenant (lead prioritization)
    op.create_index(
        'idx_leads_tenant_grade',
        'unified_leads',
        ['tenant_id', 'grade'],
        unique=False
    )
    
    # Index for follow-up scheduling (hourly cron job)
    op.create_index(
        'idx_leads_next_followup',
        'unified_leads',
        ['next_followup_at'],
        unique=False,
        postgresql_where=sa.text("next_followup_at IS NOT NULL AND status NOT IN ('WON', 'LOST')")
    )
    
    # Index for LinkedIn URL deduplication
    op.create_index(
        'idx_leads_linkedin_url',
        'unified_leads',
        ['linkedin_url'],
        unique=False,
        postgresql_where=sa.text("linkedin_url IS NOT NULL")
    )
    
    # Index for Telegram deduplication
    op.create_index(
        'idx_leads_telegram_user_id',
        'unified_leads',
        ['telegram_user_id'],
        unique=False,
        postgresql_where=sa.text("telegram_user_id IS NOT NULL")
    )
    
    # Index for WhatsApp deduplication
    op.create_index(
        'idx_leads_whatsapp_number',
        'unified_leads',
        ['whatsapp_number'],
        unique=False,
        postgresql_where=sa.text("whatsapp_number IS NOT NULL")
    )
    
    # Index for phone deduplication
    op.create_index(
        'idx_leads_phone',
        'unified_leads',
        ['phone'],
        unique=False,
        postgresql_where=sa.text("phone IS NOT NULL")
    )
    
    # Index for created_at (sorting, analytics)
    op.create_index(
        'idx_leads_created_at',
        'unified_leads',
        ['created_at'],
        unique=False
    )
    
    # Index for last_active_at (engagement tracking)
    op.create_index(
        'idx_leads_last_active',
        'unified_leads',
        ['last_active_at'],
        unique=False
    )
    
    # === LEAD_INTERACTIONS TABLE ===
    
    # Index for lead_id (foreign key)
    op.create_index(
        'idx_interactions_lead_id',
        'lead_interactions',
        ['lead_id'],
        unique=False
    )
    
    # Index for created_at (timeline queries)
    op.create_index(
        'idx_interactions_created_at',
        'lead_interactions',
        ['created_at'],
        unique=False
    )
    
    # Composite index for lead timeline
    op.create_index(
        'idx_interactions_lead_created',
        'lead_interactions',
        ['lead_id', 'created_at'],
        unique=False
    )
    
    # === PROPERTIES TABLE ===
    
    # Index for tenant isolation
    op.create_index(
        'idx_properties_tenant_id',
        'properties',
        ['tenant_id'],
        unique=False
    )
    
    # Index for active properties (listing queries)
    op.create_index(
        'idx_properties_active',
        'properties',
        ['tenant_id', 'active'],
        unique=False
    )
    
    # Index for price range queries
    op.create_index(
        'idx_properties_price',
        'properties',
        ['price'],
        unique=False
    )
    
    # Index for property type filtering
    op.create_index(
        'idx_properties_type',
        'properties',
        ['type'],
        unique=False
    )
    
    # Composite index for property matching (price + type)
    op.create_index(
        'idx_properties_price_type',
        'properties',
        ['tenant_id', 'price', 'type'],
        unique=False
    )
    
    # === PROPERTY_LEAD_MATCHES TABLE ===
    
    # Index for property_id (finding all leads for property)
    op.create_index(
        'idx_matches_property_id',
        'property_lead_matches',
        ['property_id'],
        unique=False
    )
    
    # Index for lead_id (finding all properties for lead)
    op.create_index(
        'idx_matches_lead_id',
        'property_lead_matches',
        ['lead_id'],
        unique=False
    )
    
    # Index for pending notifications
    op.create_index(
        'idx_matches_pending_notifications',
        'property_lead_matches',
        ['notified'],
        unique=False,
        postgresql_where=sa.text("notified = false")
    )
    
    # === FOLLOWUP_CAMPAIGNS TABLE ===
    
    # Index for tenant campaigns
    op.create_index(
        'idx_campaigns_tenant_id',
        'followup_campaigns',
        ['tenant_id'],
        unique=False
    )
    
    # Index for active campaigns
    op.create_index(
        'idx_campaigns_active',
        'followup_campaigns',
        ['tenant_id', 'active'],
        unique=False
    )


def downgrade():
    """Remove performance indexes"""
    
    # Drop all indexes in reverse order
    op.drop_index('idx_campaigns_active', table_name='followup_campaigns')
    op.drop_index('idx_campaigns_tenant_id', table_name='followup_campaigns')
    
    op.drop_index('idx_matches_pending_notifications', table_name='property_lead_matches')
    op.drop_index('idx_matches_lead_id', table_name='property_lead_matches')
    op.drop_index('idx_matches_property_id', table_name='property_lead_matches')
    
    op.drop_index('idx_properties_price_type', table_name='properties')
    op.drop_index('idx_properties_type', table_name='properties')
    op.drop_index('idx_properties_price', table_name='properties')
    op.drop_index('idx_properties_active', table_name='properties')
    op.drop_index('idx_properties_tenant_id', table_name='properties')
    
    op.drop_index('idx_interactions_lead_created', table_name='lead_interactions')
    op.drop_index('idx_interactions_created_at', table_name='lead_interactions')
    op.drop_index('idx_interactions_lead_id', table_name='lead_interactions')
    
    op.drop_index('idx_leads_last_active', table_name='unified_leads')
    op.drop_index('idx_leads_created_at', table_name='unified_leads')
    op.drop_index('idx_leads_phone', table_name='unified_leads')
    op.drop_index('idx_leads_whatsapp_number', table_name='unified_leads')
    op.drop_index('idx_leads_telegram_user_id', table_name='unified_leads')
    op.drop_index('idx_leads_linkedin_url', table_name='unified_leads')
    op.drop_index('idx_leads_next_followup', table_name='unified_leads')
    op.drop_index('idx_leads_tenant_grade', table_name='unified_leads')
    op.drop_index('idx_leads_tenant_status', table_name='unified_leads')
    op.drop_index('idx_leads_tenant_id', table_name='unified_leads')
