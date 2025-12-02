"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы операций
    op.create_table(
        'inventory_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(length=20), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('sku_name', sa.String(length=15), nullable=False),
        sa.Column('quantity_value', sa.Integer(), nullable=False),
        sa.Column('quantity_unit', sa.String(length=20), nullable=False),
        sa.Column('weight_value', sa.Integer(), nullable=False),
        sa.Column('weight_unit', sa.String(length=20), nullable=False),
        sa.Column('delta_value', sa.Integer(), nullable=False),
        sa.Column('delta_unit', sa.String(length=20), nullable=False),
        sa.Column('source_location', sa.String(length=100), nullable=True),
        sa.Column('target_location', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_operations_id'), 'inventory_operations', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_operations_operation_type'), 'inventory_operations', ['operation_type'], unique=False)
    op.create_index(op.f('ix_inventory_operations_sku_id'), 'inventory_operations', ['sku_id'], unique=False)
    
    # Создание таблицы абсолютных остатков по SKU
    op.create_table(
        'inventory_sku_totals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('sku_name', sa.String(length=15), nullable=False),
        sa.Column('total_quantity', sa.Integer(), nullable=False),
        sa.Column('total_weight', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_sku_totals_id'), 'inventory_sku_totals', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_sku_totals_sku_id'), 'inventory_sku_totals', ['sku_id'], unique=True)
    
    # Создание таблицы остатков по локациям
    op.create_table(
        'inventory_location_totals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('sku_name', sa.String(length=15), nullable=False),
        sa.Column('location_name', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_location_totals_id'), 'inventory_location_totals', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_location_totals_sku_id'), 'inventory_location_totals', ['sku_id'], unique=False)
    op.create_index(op.f('ix_inventory_location_totals_location_name'), 'inventory_location_totals', ['location_name'], unique=False)
    # Уникальный индекс на комбинацию sku_id + location_name
    op.create_index('uq_inventory_location_sku_location', 'inventory_location_totals', ['sku_id', 'location_name'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_inventory_location_sku_location', table_name='inventory_location_totals')
    op.drop_index(op.f('ix_inventory_location_totals_location_name'), table_name='inventory_location_totals')
    op.drop_index(op.f('ix_inventory_location_totals_sku_id'), table_name='inventory_location_totals')
    op.drop_index(op.f('ix_inventory_location_totals_id'), table_name='inventory_location_totals')
    op.drop_table('inventory_location_totals')
    
    op.drop_index(op.f('ix_inventory_sku_totals_sku_id'), table_name='inventory_sku_totals')
    op.drop_index(op.f('ix_inventory_sku_totals_id'), table_name='inventory_sku_totals')
    op.drop_table('inventory_sku_totals')
    
    op.drop_index(op.f('ix_inventory_operations_sku_id'), table_name='inventory_operations')
    op.drop_index(op.f('ix_inventory_operations_operation_type'), table_name='inventory_operations')
    op.drop_index(op.f('ix_inventory_operations_id'), table_name='inventory_operations')
    op.drop_table('inventory_operations')

