"""Change status to string

Revision ID: 002_change_status
Revises: 001_initial
Create Date: 2024-12-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_change_status'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Изменяем тип колонки status с enum на String
    # Сначала конвертируем существующие значения enum в строки
    op.execute("""
        ALTER TABLE skus 
        ALTER COLUMN status TYPE VARCHAR(20) 
        USING CASE 
            WHEN status::text = 'available' THEN 'available'
            WHEN status::text = 'unavailable' THEN 'unavailable'
            WHEN status::text = 'unknown' THEN 'unknown'
            ELSE 'unknown'
        END
    """)
    
    # Удаляем enum тип (если он больше не используется)
    # op.execute('DROP TYPE IF EXISTS skustatus')


def downgrade() -> None:
    # Восстанавливаем enum тип
    skustatus_enum = postgresql.ENUM('available', 'unavailable', 'unknown', name='skustatus', create_type=True)
    skustatus_enum.create(op.get_bind(), checkfirst=True)
    
    # Конвертируем строки обратно в enum
    op.execute("""
        ALTER TABLE skus 
        ALTER COLUMN status TYPE skustatus 
        USING status::skustatus
    """)


