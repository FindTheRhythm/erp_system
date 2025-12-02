"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-01

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
    # Создание enum типов (с проверкой существования)
    conn = op.get_bind()
    
    # Проверяем и создаем unittype если не существует
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'unittype'"))
    if result.fetchone() is None:
        unittype_enum = postgresql.ENUM('weight', 'quantity', 'price', name='unittype', create_type=True)
        unittype_enum.create(conn, checkfirst=False)
    
    # Проверяем и создаем skustatus если не существует
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'skustatus'"))
    if result.fetchone() is None:
        skustatus_enum = postgresql.ENUM('available', 'unavailable', 'unknown', name='skustatus', create_type=True)
        skustatus_enum.create(conn, checkfirst=False)
    
    # Используем существующие или созданные типы
    unittype_enum = postgresql.ENUM('weight', 'quantity', 'price', name='unittype', create_type=False)
    skustatus_enum = postgresql.ENUM('available', 'unavailable', 'unknown', name='skustatus', create_type=False)
    
    # Создание таблицы единиц измерения
    op.create_table(
        'units',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=20), nullable=False),
        sa.Column('type', unittype_enum, nullable=False),
        sa.Column('description', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_units_id'), 'units', ['id'], unique=False)
    op.create_index(op.f('ix_units_name'), 'units', ['name'], unique=True)
    
    # Создание таблицы товаров (SKU)
    op.create_table(
        'skus',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=9), nullable=False),
        sa.Column('name', sa.String(length=15), nullable=False),
        sa.Column('weight', sa.String(length=5), nullable=False),
        sa.Column('weight_unit_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.String(length=5), nullable=False),
        sa.Column('quantity_unit_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=120), nullable=True),
        sa.Column('price', sa.String(length=5), nullable=True),
        sa.Column('price_unit_id', sa.Integer(), nullable=True),
        sa.Column('status', skustatus_enum, nullable=True),
        sa.Column('photo_url', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['price_unit_id'], ['units.id'], ),
        sa.ForeignKeyConstraint(['quantity_unit_id'], ['units.id'], ),
        sa.ForeignKeyConstraint(['weight_unit_id'], ['units.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skus_id'), 'skus', ['id'], unique=False)
    op.create_index(op.f('ix_skus_code'), 'skus', ['code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_skus_code'), table_name='skus')
    op.drop_index(op.f('ix_skus_id'), table_name='skus')
    op.drop_table('skus')
    op.drop_index(op.f('ix_units_name'), table_name='units')
    op.drop_index(op.f('ix_units_id'), table_name='units')
    op.drop_table('units')
    op.execute('DROP TYPE IF EXISTS skustatus')
    op.execute('DROP TYPE IF EXISTS unittype')

