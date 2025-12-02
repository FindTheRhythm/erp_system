"""
Скрипт для заполнения начальных данных (единицы измерения)
Запускается после миграций
"""
from app.database import SessionLocal
from app.models import Unit, UnitType

def init_units():
    """Создать базовые единицы измерения"""
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже единицы
        if db.query(Unit).count() > 0:
            print("Единицы измерения уже существуют, пропускаем инициализацию")
            return
        
        # Единицы веса
        weight_units = [
            Unit(name="кг", type=UnitType.weight, description="Килограмм"),
            Unit(name="г", type=UnitType.weight, description="Грамм"),
            Unit(name="т", type=UnitType.weight, description="Тонна"),
        ]
        
        # Единицы количества
        quantity_units = [
            Unit(name="шт", type=UnitType.quantity, description="Штука"),
            Unit(name="уп", type=UnitType.quantity, description="Упаковка"),
            Unit(name="ящ", type=UnitType.quantity, description="Ящик"),
            Unit(name="пал", type=UnitType.quantity, description="Паллета"),
        ]
        
        # Единицы цены
        price_units = [
            Unit(name="руб", type=UnitType.price, description="Рубль"),
            Unit(name="USD", type=UnitType.price, description="Доллар США"),
            Unit(name="EUR", type=UnitType.price, description="Евро"),
        ]
        
        all_units = weight_units + quantity_units + price_units
        
        for unit in all_units:
            db.add(unit)
        
        db.commit()
        print(f"Создано {len(all_units)} единиц измерения")
        
    except Exception as e:
        print(f"Ошибка при инициализации единиц измерения: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_units()


