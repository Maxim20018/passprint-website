"""Add audit and backup tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-04 09:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create audit_logs table
    op.create_table('audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create system_config table
    op.create_table('system_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('data_type', sa.String(length=20), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

    # Create backup_logs table
    op.create_table('backup_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backup_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better performance
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_action', 'audit_log', ['action'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])
    op.create_index('ix_audit_log_resource_type', 'audit_log', ['resource_type'])

    op.create_index('ix_system_config_key', 'system_config', ['key'])

    op.create_index('ix_backup_log_backup_type', 'backup_log', ['backup_type'])
    op.create_index('ix_backup_log_status', 'backup_log', ['status'])
    op.create_index('ix_backup_log_started_at', 'backup_log', ['started_at'])

def downgrade():
    # Drop indexes first
    op.drop_index('ix_backup_log_started_at', table_name='backup_log')
    op.drop_index('ix_backup_log_status', table_name='backup_log')
    op.drop_index('ix_backup_log_backup_type', table_name='backup_log')

    op.drop_index('ix_system_config_key', table_name='system_config')

    op.drop_index('ix_audit_log_resource_type', table_name='audit_log')
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_index('ix_audit_log_action', table_name='audit_log')
    op.drop_index('ix_audit_log_user_id', table_name='audit_log')

    # Drop tables
    op.drop_table('backup_log')
    op.drop_table('system_config')
    op.drop_table('audit_log')