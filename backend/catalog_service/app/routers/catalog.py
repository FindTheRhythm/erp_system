from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import logging
import csv
import io

from app.database import get_db
from app.models import SKU, Unit, SKUStatus
from app.schemas import (
    SKUCreate, SKUUpdate, SKUResponse, SKUListResponse,
    UnitCreate, UnitResponse
)
from app.rabbitmq_client import rabbitmq_client
from app.dependencies import get_user_role, require_admin_role
from app.inventory_client import create_inventory_operation, get_sku_total_weight

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["catalog"])


# ========== SKU Endpoints ==========

@router.get("/skus", response_model=List[SKUListResponse])
async def get_skus(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Поиск по названию или артикулу"),
    status: Optional[SKUStatus] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db)
):
    """Получить список товаров"""
    query = db.query(SKU)
    
    # Поиск
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                SKU.name.ilike(search_term),
                SKU.code.ilike(search_term)
            )
        )
    
    # Фильтр по статусу
    if status:
        # Преобразуем enum в строку для сравнения
        status_str = status.value if isinstance(status, SKUStatus) else str(status).lower()
        query = query.filter(SKU.status == status_str)
    
    # Пагинация
    skus = query.offset(skip).limit(limit).all()
    return skus


@router.get("/skus/{sku_id}", response_model=SKUResponse)
async def get_sku(sku_id: int, db: Session = Depends(get_db)):
    """Получить товар по ID"""
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return sku


@router.get("/skus/search", response_model=List[SKUListResponse])
async def search_skus(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Поиск товаров"""
    search_term = f"%{q}%"
    skus = db.query(SKU).filter(
        or_(
            SKU.name.ilike(search_term),
            SKU.code.ilike(search_term),
            SKU.description.ilike(search_term)
        )
    ).limit(limit).all()
    return skus


@router.post("/skus", response_model=SKUResponse, status_code=201)
async def create_sku(
    sku: SKUCreate, 
    db: Session = Depends(get_db),
    user_role: str = Depends(get_user_role)
):
    """Создать товар (только для admin)"""
    require_admin_role(user_role)
    
    # Проверка уникальности артикула (вторая часть должна быть уникальной)
    existing_sku = db.query(SKU).filter(SKU.code == sku.code).first()
    if existing_sku:
        raise HTTPException(status_code=400, detail="Товар с таким артикулом уже существует")
    
    # Проверка существования единиц измерения
    weight_unit = db.query(Unit).filter(Unit.id == sku.weight_unit_id).first()
    if not weight_unit:
        raise HTTPException(status_code=404, detail="Единица измерения веса не найдена")
    
    quantity_unit = db.query(Unit).filter(Unit.id == sku.quantity_unit_id).first()
    if not quantity_unit:
        raise HTTPException(status_code=404, detail="Единица измерения количества не найдена")
    
    if sku.price_unit_id:
        price_unit = db.query(Unit).filter(Unit.id == sku.price_unit_id).first()
        if not price_unit:
            raise HTTPException(status_code=404, detail="Единица измерения цены не найдена")
    
    # Создание товара
    # Получаем статус и преобразуем в строку (нижний регистр)
    status_value = sku.status if sku.status else SKUStatus.UNKNOWN
    
    # Преобразуем статус в строку (нижний регистр)
    if isinstance(status_value, SKUStatus):
        status_str = status_value.value  # Получаем значение enum (например, "unknown")
    elif isinstance(status_value, str):
        status_str = status_value.lower()  # Приводим к нижнему регистру
    else:
        status_str = "unknown"
    
    # Валидация статуса
    if status_str not in ["available", "unavailable", "unknown"]:
        logger.warning(f"Invalid status value: {status_str}, using 'unknown'")
        status_str = "unknown"
    
    logger.info(f"Creating SKU with status: {status_str}")
    
    # Создаем объект SKU, передавая статус как строку
    db_sku = SKU(
        code=sku.code,
        name=sku.name,
        weight=sku.weight,
        weight_unit_id=sku.weight_unit_id,
        quantity=sku.quantity,
        quantity_unit_id=sku.quantity_unit_id,
        description=sku.description,
        price=sku.price,
        price_unit_id=sku.price_unit_id,
        status=status_str,  # Передаем как строку
        photo_url=sku.photo_url
    )
    db.add(db_sku)
    db.commit()
    db.refresh(db_sku)
    
    # Отправка события в RabbitMQ
    rabbitmq_client.publish_event("created", {
        "sku_id": db_sku.id,
        "code": db_sku.code,
        "name": db_sku.name
    })
    
    # Создание операции в Inventory Service
    try:
        quantity_value = int(float(db_sku.quantity))
        weight_value = int(float(db_sku.weight))
        quantity_unit_name = db_sku.quantity_unit.name if db_sku.quantity_unit else 'шт'
        weight_unit_name = db_sku.weight_unit.name if db_sku.weight_unit else 'кг'
        
        await create_inventory_operation(
            operation_type='create',
            sku_id=db_sku.id,
            quantity_value=quantity_value,
            quantity_unit=quantity_unit_name,
            weight_value=weight_value,
            weight_unit=weight_unit_name,
            source_location='хранилище'
        )
    except Exception as e:
        logger.error(f"Error creating inventory operation for SKU {db_sku.id}: {e}")
        # Не прерываем создание товара, если операция в Inventory не создалась
    
    logger.info(f"Created SKU: {db_sku.code} - {db_sku.name}")
    return db_sku


@router.put("/skus/{sku_id}", response_model=SKUResponse)
async def update_sku(
    sku_id: int,
    sku_update: SKUUpdate,
    db: Session = Depends(get_db),
    user_role: str = Depends(get_user_role)
):
    """Обновить товар (только для admin)"""
    require_admin_role(user_role)
    
    db_sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not db_sku:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Обновление полей
    update_data = sku_update.dict(exclude_unset=True)
    
    # Проверка единиц измерения если они обновляются
    if "weight_unit_id" in update_data:
        unit = db.query(Unit).filter(Unit.id == update_data["weight_unit_id"]).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Единица измерения веса не найдена")
    
    if "quantity_unit_id" in update_data:
        unit = db.query(Unit).filter(Unit.id == update_data["quantity_unit_id"]).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Единица измерения количества не найдена")
    
    if "price_unit_id" in update_data and update_data["price_unit_id"]:
        unit = db.query(Unit).filter(Unit.id == update_data["price_unit_id"]).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Единица измерения цены не найдена")
    
    for field, value in update_data.items():
        # Преобразуем статус в строку (нижний регистр), если он обновляется
        if field == 'status' and value:
            if isinstance(value, SKUStatus):
                setattr(db_sku, field, value.value)  # Получаем значение enum
            elif isinstance(value, str):
                setattr(db_sku, field, value.lower())  # Приводим к нижнему регистру
            else:
                setattr(db_sku, field, "unknown")
        else:
            setattr(db_sku, field, value)
    
    db.commit()
    db.refresh(db_sku)
    
    # Отправка события в RabbitMQ
    rabbitmq_client.publish_event("updated", {
        "sku_id": db_sku.id,
        "code": db_sku.code,
        "name": db_sku.name
    })
    
    # Создание операции в Inventory Service
    try:
        quantity_value = int(float(db_sku.quantity))
        weight_value = int(float(db_sku.weight))
        quantity_unit_name = db_sku.quantity_unit.name if db_sku.quantity_unit else 'шт'
        weight_unit_name = db_sku.weight_unit.name if db_sku.weight_unit else 'кг'
        
        await create_inventory_operation(
            operation_type='update',
            sku_id=db_sku.id,
            quantity_value=quantity_value,
            quantity_unit=quantity_unit_name,
            weight_value=weight_value,
            weight_unit=weight_unit_name,
            source_location='хранилище'
        )
    except Exception as e:
        logger.error(f"Error creating inventory operation for updated SKU {db_sku.id}: {e}")
        # Не прерываем обновление товара, если операция в Inventory не создалась
    
    logger.info(f"Updated SKU: {db_sku.code} - {db_sku.name}")
    return db_sku


@router.delete("/skus/{sku_id}", status_code=204)
async def delete_sku(
    sku_id: int, 
    db: Session = Depends(get_db),
    user_role: str = Depends(get_user_role)
):
    """Удалить товар (только для admin)"""
    require_admin_role(user_role)
    
    db_sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not db_sku:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    sku_code = db_sku.code
    sku_name = db_sku.name
    
    db.delete(db_sku)
    db.commit()
    
    # Отправка события в RabbitMQ
    rabbitmq_client.publish_event("deleted", {
        "sku_id": sku_id,
        "code": sku_code,
        "name": sku_name
    })
    
    # Создание операции в Inventory Service
    # Получаем текущее итоговое значение из остатков перед удалением
    try:
        total_weight = await get_sku_total_weight(sku_id)
        if total_weight is None or total_weight == 0:
            # Если остатков нет, используем значения из товара
            total_weight = 0
            quantity_value = 0
        else:
            # Используем текущее значение как weight_value
            quantity_value = 1  # Минимальное значение для отображения
        
        await create_inventory_operation(
            operation_type='delete',
            sku_id=sku_id,
            quantity_value=quantity_value,
            quantity_unit='шт',
            weight_value=total_weight,  # Используем текущее итоговое значение
            weight_unit='кг',
            source_location='хранилище'
        )
    except Exception as e:
        logger.error(f"Error creating inventory operation for deleted SKU {sku_id}: {e}")
        # Не прерываем удаление товара, если операция в Inventory не создалась
    
    logger.info(f"Deleted SKU: {sku_code} - {sku_name}")
    return None


# ========== Units Endpoints ==========

@router.get("/units", response_model=List[UnitResponse])
async def get_units(
    type: Optional[str] = Query(None, description="Фильтр по типу: weight, quantity, price"),
    db: Session = Depends(get_db)
):
    """Получить список единиц измерения"""
    query = db.query(Unit)
    if type:
        query = query.filter(Unit.type == type)
    return query.all()


@router.post("/units", response_model=UnitResponse, status_code=201)
async def create_unit(
    unit: UnitCreate, 
    db: Session = Depends(get_db),
    user_role: str = Depends(get_user_role)
):
    """Создать единицу измерения (только для admin)"""
    require_admin_role(user_role)
    
    # Проверка уникальности названия
    existing_unit = db.query(Unit).filter(Unit.name == unit.name).first()
    if existing_unit:
        raise HTTPException(status_code=400, detail="Единица измерения с таким названием уже существует")
    
    db_unit = Unit(**unit.dict())
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    
    return db_unit


# ========== CSV Import/Export ==========

@router.get("/skus/export/csv")
async def export_skus_csv(db: Session = Depends(get_db)):
    """Экспорт товаров в CSV"""
    skus = db.query(SKU).all()
    
    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        "ID", "Артикул", "Название", "Вес", "Ед. веса", 
        "Количество", "Ед. количества", "Описание", 
        "Цена", "Ед. цены", "Статус", "Фото URL"
    ])
    
    # Данные
    for sku in skus:
        writer.writerow([
            sku.id,
            sku.code,
            sku.name,
            sku.weight,
            sku.weight_unit.name if sku.weight_unit else "",
            sku.quantity,
            sku.quantity_unit.name if sku.quantity_unit else "",
            sku.description or "",
            sku.price or "",
            sku.price_unit.name if sku.price_unit else "",
            sku.status.value if sku.status else "",
            sku.photo_url or ""
        ])
    
    output.seek(0)
    
    # Возвращаем CSV файл
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=skus_export.csv"}
    )


@router.post("/skus/import/csv")
async def import_skus_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_role: str = Depends(get_user_role)
):
    """Импорт товаров из CSV"""
    require_admin_role(user_role)
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате CSV")
    
    # Читаем файл
    contents = await file.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    reader = csv.DictReader(csv_data)
    
    imported = 0
    errors = []
    
    # Получаем единицы измерения для маппинга
    units_by_name = {}
    for unit in db.query(Unit).all():
        units_by_name[unit.name.lower()] = unit
    
    for row_num, row in enumerate(reader, start=2):  # Начинаем с 2, т.к. 1 - заголовок
        try:
            # Парсим данные
            code = row.get("Артикул", "").strip()
            name = row.get("Название", "").strip()
            weight = row.get("Вес", "").strip()
            weight_unit_name = row.get("Ед. веса", "").strip()
            quantity = row.get("Количество", "").strip()
            quantity_unit_name = row.get("Ед. количества", "").strip()
            description = row.get("Описание", "").strip()
            price = row.get("Цена", "").strip() or None
            price_unit_name = row.get("Ед. цены", "").strip() or None
            status_str = row.get("Статус", "").strip() or "unknown"
            photo_url = row.get("Фото URL", "").strip() or None
            
            # Валидация обязательных полей
            if not code or not name or not weight or not quantity:
                errors.append(f"Строка {row_num}: Отсутствуют обязательные поля")
                continue
            
            # Проверка существования товара
            existing_sku = db.query(SKU).filter(SKU.code == code.upper()).first()
            if existing_sku:
                errors.append(f"Строка {row_num}: Товар с артикулом {code} уже существует")
                continue
            
            # Получение единиц измерения
            weight_unit = units_by_name.get(weight_unit_name.lower())
            if not weight_unit:
                errors.append(f"Строка {row_num}: Единица измерения веса '{weight_unit_name}' не найдена")
                continue
            
            quantity_unit = units_by_name.get(quantity_unit_name.lower())
            if not quantity_unit:
                errors.append(f"Строка {row_num}: Единица измерения количества '{quantity_unit_name}' не найдена")
                continue
            
            price_unit = None
            if price_unit_name:
                price_unit = units_by_name.get(price_unit_name.lower())
                if not price_unit:
                    errors.append(f"Строка {row_num}: Единица измерения цены '{price_unit_name}' не найдена")
                    continue
            
            # Маппинг статуса в строку (нижний регистр)
            status_map = {
                "available": "available",
                "unavailable": "unavailable",
                "unknown": "unknown",
                "есть": "available",
                "отсутствует": "unavailable",
                "неизвестно": "unknown"
            }
            status = status_map.get(status_str.lower(), "unknown")
            
            # Создание товара
            sku = SKU(
                code=code.upper(),
                name=name[:15],  # Ограничение длины
                weight=weight[:5],
                weight_unit_id=weight_unit.id,
                quantity=quantity[:5],
                quantity_unit_id=quantity_unit.id,
                description=description[:120] if description else None,
                price=price[:5] if price else None,
                price_unit_id=price_unit.id if price_unit else None,
                status=status,
                photo_url=photo_url[:255] if photo_url else None
            )
            
            db.add(sku)
            imported += 1
            
        except Exception as e:
            errors.append(f"Строка {row_num}: Ошибка - {str(e)}")
            logger.error(f"Error importing row {row_num}: {e}")
    
    db.commit()
    
    return {
        "imported": imported,
        "errors": errors,
        "message": f"Импортировано {imported} товаров" + (f", ошибок: {len(errors)}" if errors else "")
    }

