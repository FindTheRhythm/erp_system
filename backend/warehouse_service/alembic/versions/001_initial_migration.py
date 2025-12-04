"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-04

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
    # Создание enum типов
    conn = op.get_bind()
    
    # Проверяем и создаем locationtype если не существует
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'locationtype'"))
    if result.fetchone() is None:
        locationtype_enum = postgresql.ENUM('storage', 'warehouse', 'temp_storage', name='locationtype', create_type=True)
        locationtype_enum.create(conn, checkfirst=False)
    
    # Проверяем и создаем operationtype если не существует
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'operationtype'"))
    if result.fetchone() is None:
        operationtype_enum = postgresql.ENUM(
            'receipt', 'shipment', 'transfer',
            'global_distribution_all', 'global_distribution_sku',
            'replenishment_all', 'replenishment_sku',
            'placement_all', 'placement_sku',
            name='operationtype', create_type=True
        )
        operationtype_enum.create(conn, checkfirst=False)
    
    # Используем существующие или созданные типы
    locationtype_enum = postgresql.ENUM('storage', 'warehouse', 'temp_storage', name='locationtype', create_type=False)
    operationtype_enum = postgresql.ENUM(
        'receipt', 'shipment', 'transfer',
        'global_distribution_all', 'global_distribution_sku',
        'replenishment_all', 'replenishment_sku',
        'placement_all', 'placement_sku',
        name='operationtype', create_type=False
    )
    
    # Создание таблицы локаций
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', locationtype_enum, nullable=False),
        sa.Column('max_capacity_kg', sa.Integer(), nullable=False),
        sa.Column('current_capacity_kg', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=True)
    
    # Создание таблицы операций
    op.create_table(
        'warehouse_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation_type', operationtype_enum, nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=True),
        sa.Column('sku_name', sa.String(length=15), nullable=True),
        sa.Column('source_location_id', sa.Integer(), nullable=True),
        sa.Column('target_location_id', sa.Integer(), nullable=True),
        sa.Column('quantity_kg', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['target_location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_warehouse_operations_id'), 'warehouse_operations', ['id'], unique=False)
    op.create_index(op.f('ix_warehouse_operations_sku_id'), 'warehouse_operations', ['sku_id'], unique=False)
    
    # Создание таблицы временного хранилища
    op.create_table(
        'temp_storage_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('sku_name', sa.String(length=15), nullable=False),
        sa.Column('quantity_kg', sa.Integer(), nullable=False),
        sa.Column('source_operation_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('moved_to_storage_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_operation_id'], ['warehouse_operations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_temp_storage_items_id'), 'temp_storage_items', ['id'], unique=False)
    op.create_index(op.f('ix_temp_storage_items_sku_id'), 'temp_storage_items', ['sku_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_temp_storage_items_sku_id'), table_name='temp_storage_items')
    op.drop_index(op.f('ix_temp_storage_items_id'), table_name='temp_storage_items')
    op.drop_table('temp_storage_items')
    
    op.drop_index(op.f('ix_warehouse_operations_sku_id'), table_name='warehouse_operations')
    op.drop_index(op.f('ix_warehouse_operations_id'), table_name='warehouse_operations')
    op.drop_table('warehouse_operations')
    
    op.drop_index(op.f('ix_locations_name'), table_name='locations')
    op.drop_index(op.f('ix_locations_id'), table_name='locations')
    op.drop_table('locations')
    
    # Удаляем enum типы
    op.execute("DROP TYPE IF EXISTS operationtype")
    op.execute("DROP TYPE IF EXISTS locationtype")
