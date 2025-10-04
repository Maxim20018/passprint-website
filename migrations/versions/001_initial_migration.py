"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-04 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('company', sa.String(length=100), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create products table
    op.create_table('product',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('stock_quantity', sa.Integer(), nullable=True),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create orders table
    op.create_table('order',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(length=20), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('payment_status', sa.String(length=20), nullable=True),
        sa.Column('stripe_payment_id', sa.String(length=100), nullable=True),
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('shipping_phone', sa.String(length=20), nullable=True),
        sa.Column('shipping_email', sa.String(length=120), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number')
    )

    # Create order_items table
    op.create_table('order_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('specifications', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create quotes table
    op.create_table('quote',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quote_number', sa.String(length=20), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('project_name', sa.String(length=100), nullable=True),
        sa.Column('project_description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.String(length=50), nullable=True),
        sa.Column('format', sa.String(length=20), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('material', sa.String(length=50), nullable=True),
        sa.Column('finishing', sa.String(length=100), nullable=True),
        sa.Column('estimated_price', sa.Float(), nullable=True),
        sa.Column('final_price', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('files', sa.Text(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quote_number')
    )

    # Create carts table
    op.create_table('cart',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('items', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create files table
    op.create_table('file',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('pages', sa.Integer(), nullable=True),
        sa.Column('quote_id', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
        sa.ForeignKeyConstraint(['quote_id'], ['quote.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create newsletter_subscribers table
    op.create_table('newsletter_subscriber',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=True),
        sa.Column('last_name', sa.String(length=50), nullable=True),
        sa.Column('subscribed_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

def downgrade():
    # Drop tables in reverse order
    op.drop_table('newsletter_subscriber')
    op.drop_table('file')
    op.drop_table('cart')
    op.drop_table('quote')
    op.drop_table('order_item')
    op.drop_table('order')
    op.drop_table('product')
    op.drop_table('user')