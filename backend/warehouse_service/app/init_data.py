"""
Скрипт для заполнения начальных данных (локации)
Запускается после миграций
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import Location, LocationType

def init_locations():
    """Создать базовые локации"""
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже локации
        if db.query(Location).count() > 0:
            print("Локации уже существуют, пропускаем инициализацию")
            return
        
        # Материнское хранилище (основное, где создаются товары по умолчанию)
        locations = [
            Location(
                name="Материнское хранилище",
                type=LocationType.STORAGE,
                max_capacity_kg=1000000,  # 1000 тонн
                current_capacity_kg=0,
                description="Основное хранилище, где создаются товары по умолчанию"
            ),
            # 4 склада
            Location(
                name="Альфа",
                type=LocationType.WAREHOUSE,
                max_capacity_kg=50000,  # 50 тонн
                current_capacity_kg=0,
                description="Склад Альфа"
            ),
            Location(
                name="Бета",
                type=LocationType.WAREHOUSE,
                max_capacity_kg=50000,  # 50 тонн
                current_capacity_kg=0,
                description="Склад Бета"
            ),
            Location(
                name="Чарли",
                type=LocationType.WAREHOUSE,
                max_capacity_kg=50000,  # 50 тонн
                current_capacity_kg=0,
                description="Склад Чарли"
            ),
            Location(
                name="Дельта",
                type=LocationType.WAREHOUSE,
                max_capacity_kg=50000,  # 50 тонн
                current_capacity_kg=0,
                description="Склад Дельта"
            ),
            # Временное хранилище
            Location(
                name="Временное хранилище",
                type=LocationType.TEMP_STORAGE,
                max_capacity_kg=20000,  # 20 тонн для временного хранения
                current_capacity_kg=0,
                description="Временное хранилище для излишков товаров"
            ),
        ]
        
        for location in locations:
            db.add(location)
        
        db.commit()
        print(f"Создано {len(locations)} локаций")
        
    except Exception as e:
        print(f"Ошибка при инициализации локаций: {e}")
        db.rollback()
    finally:
        db.close()

