"""
Скрипт для заполнения начальных данных (тестовые товары в локациях)
Запускается после миграций
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import InventoryLocationTotal, InventorySKUTotal

def init_location_items():
    """Создать тестовые товары в локациях"""
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже товары в локациях
        if db.query(InventoryLocationTotal).count() > 0:
            print("Товары в локациях уже существуют, пропускаем инициализацию")
            return
        
        # Товары машинной тематики (названия до 15 символов)
        car_items = [
            { 'id': 1, 'name': 'Двигатель V8' },
            { 'id': 2, 'name': 'Коробка передач' },
            { 'id': 3, 'name': 'Радиатор охл' },
            { 'id': 4, 'name': 'Тормозные кол' },
            { 'id': 5, 'name': 'Аккумулятор' },
            { 'id': 6, 'name': 'Генератор' },
            { 'id': 7, 'name': 'Карбюратор' },
            { 'id': 8, 'name': 'Шины R17' },
            { 'id': 9, 'name': 'Амортизаторы' },
            { 'id': 10, 'name': 'Рулевая рейка' },
            { 'id': 11, 'name': 'Масл. фильтр' },
            { 'id': 12, 'name': 'Возд. фильтр' },
        ]
        
        # Локации с их заполненностью
        locations_config = {
            'Материнское хранилище': {
                'max_capacity': 1000000,
                'fill_percentage': 0.35,  # 35%
                'items_count': 10,
            },
            'Альфа': {
                'max_capacity': 50000,
                'fill_percentage': 0.95,  # 95% - почти полностью
                'items_count': 10,
            },
            'Бета': {
                'max_capacity': 50000,
                'fill_percentage': 0.75,  # 75%
                'items_count': 8,
            },
            'Чарли': {
                'max_capacity': 50000,
                'fill_percentage': 0.45,  # 45%
                'items_count': 7,
            },
            'Дельта': {
                'max_capacity': 50000,
                'fill_percentage': 0.25,  # 25%
                'items_count': 6,
            },
            'Временное хранилище': {
                'max_capacity': 20000,
                'fill_percentage': 0.15,  # 15%
                'items_count': 5,
            },
        }
        
        # Создаем товары для каждой локации
        for location_name, config in locations_config.items():
            total_weight = int(config['max_capacity'] * config['fill_percentage'])
            items_count = min(config['items_count'], len(car_items))
            
            # Распределяем вес неравномерно
            weights = []
            remaining = total_weight
            for i in range(items_count):
                if i == items_count - 1:
                    weights.append(remaining)
                else:
                    base_weight = total_weight // items_count
                    weight = int(base_weight * (0.6 + (i % 3) * 0.2))  # Вариация весов
                    weights.append(weight)
                    remaining -= weight
            
            # Сортируем по убыванию для реалистичности
            weights.sort(reverse=True)
            
            # Создаем записи товаров в локации
            for i in range(items_count):
                item = car_items[i]
                location_total = InventoryLocationTotal(
                    sku_id=item['id'],
                    sku_name=item['name'],
                    location_name=location_name,
                    quantity=weights[i] // 10,  # Примерное количество
                    weight=weights[i],
                )
                db.add(location_total)
                
                # Обновляем или создаем SKU total
                sku_total = db.query(InventorySKUTotal).filter(
                    InventorySKUTotal.sku_id == item['id']
                ).first()
                
                if sku_total:
                    sku_total.total_weight += weights[i]
                    sku_total.total_quantity += (weights[i] // 10)
                    sku_total.sku_name = item['name']  # Обновляем название
                else:
                    sku_total = InventorySKUTotal(
                        sku_id=item['id'],
                        sku_name=item['name'],
                        total_quantity=weights[i] // 10,
                        total_weight=weights[i],
                    )
                    db.add(sku_total)
        
        db.commit()
        print(f"Созданы тестовые товары для {len(locations_config)} локаций")
        
    except Exception as e:
        print(f"Ошибка при инициализации товаров: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


