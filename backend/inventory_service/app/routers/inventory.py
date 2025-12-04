from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import logging

from app.database import get_db
from app.models import InventoryOperation, InventorySKUTotal, InventoryLocationTotal
from app.schemas import OperationCreate, OperationResponse, SKUTotalResponse, LocationTotalResponse
from app.inventory_service import InventoryService
from app.rabbitmq_client import rabbitmq_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/", summary="Справка по Inventory API")
async def inventory_root():
    """Базовый endpoint Inventory Service (для проверки через API Gateway)."""
    return {
        "message": "Inventory Service API",
        "available_endpoints": {
            "operations": {
                "list": "GET /inventory/operations",
                "create": "POST /inventory/operations"
            },
            "sku_totals": "GET /inventory/sku/totals",
            "location_totals": "GET /inventory/locations",
            "location_details": "GET /inventory/locations/{location_name}",
            "sku_history": "GET /inventory/sku/{sku_id}/history"
        }
    }


@router.post("/operations", response_model=OperationResponse, status_code=201)
async def create_operation(
    operation: OperationCreate,
    db: Session = Depends(get_db)
):
    """
    Создать операцию с товаром.
    Используется другими сервисами (Catalog, Warehouse, Orders) для записи операций.
    """
    try:
        # Для операции delete получаем текущее итоговое значение из остатков
        if operation.operation_type == 'delete':
            sku_total = db.query(InventorySKUTotal).filter(InventorySKUTotal.sku_id == operation.sku_id).first()
            if sku_total:
                # Используем текущее значение как delta_value (будет отрицательным при удалении)
                # Переопределяем quantity_value и weight_value для правильного отображения
                quantity_value = sku_total.total_quantity if sku_total.total_quantity > 0 else 1
                weight_value = sku_total.total_weight if sku_total.total_weight > 0 else operation.weight_value
                # Создаем операцию с переопределенным delta_value (отрицательное значение)
                db_operation = await InventoryService.create_operation_with_delta(
                    db=db,
                    operation_type=operation.operation_type,
                    sku_id=operation.sku_id,
                    quantity_value=quantity_value,
                    quantity_unit=operation.quantity_unit,
                    weight_value=weight_value,
                    weight_unit=operation.weight_unit,
                    delta_value=-sku_total.total_weight if sku_total.total_weight > 0 else 0,  # Отрицательное значение при удалении
                    source_location=operation.source_location,
                    target_location=operation.target_location
                )
            else:
                # Если остатков нет, все равно создаем операцию для истории
                # Используем переданные значения или значения по умолчанию
                db_operation = await InventoryService.create_operation_with_delta(
                    db=db,
                    operation_type=operation.operation_type,
                    sku_id=operation.sku_id,
                    quantity_value=operation.quantity_value or 0,
                    quantity_unit=operation.quantity_unit or 'шт',
                    weight_value=operation.weight_value or 0,
                    weight_unit=operation.weight_unit or 'кг',
                    delta_value=0,
                    source_location=operation.source_location,
                    target_location=operation.target_location
                )
        else:
            # Для других операций создаем как обычно
            db_operation = await InventoryService.create_operation(
                db=db,
                operation_type=operation.operation_type,
                sku_id=operation.sku_id,
                quantity_value=operation.quantity_value,
                quantity_unit=operation.quantity_unit,
                weight_value=operation.weight_value,
                weight_unit=operation.weight_unit,
                source_location=operation.source_location,
                target_location=operation.target_location
            )
        
        # Публикуем событие в RabbitMQ
        rabbitmq_client.publish_event("operation.created", {
            "operation_id": db_operation.id,
            "operation_type": db_operation.operation_type,
            "sku_id": db_operation.sku_id,
            "sku_name": db_operation.sku_name,
            "delta_value": db_operation.delta_value,
            "delta_unit": db_operation.delta_unit,
            "source_location": db_operation.source_location,
            "target_location": db_operation.target_location
        })
        
        return db_operation
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating operation: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании операции")


@router.get("/operations", response_model=List[OperationResponse])
async def get_operations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    operation_type: Optional[str] = Query(None, description="Фильтр по типу операции"),
    sku_id: Optional[int] = Query(None, description="Фильтр по ID товара"),
    location: Optional[str] = Query(None, description="Фильтр по локации"),
    db: Session = Depends(get_db)
):
    """Получить список операций"""
    query = db.query(InventoryOperation)
    
    # Фильтры
    if operation_type:
        query = query.filter(InventoryOperation.operation_type == operation_type)
    
    if sku_id:
        query = query.filter(InventoryOperation.sku_id == sku_id)
    
    if location:
        query = query.filter(
            or_(
                InventoryOperation.source_location == location,
                InventoryOperation.target_location == location
            )
        )
    
    # Сортировка по дате создания (новые сначала)
    query = query.order_by(InventoryOperation.created_at.desc())
    
    # Пагинация
    operations = query.offset(skip).limit(limit).all()
    return operations


@router.get("/sku/totals", response_model=List[SKUTotalResponse])
async def get_sku_totals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sku_id: Optional[int] = Query(None, description="Фильтр по ID товара"),
    db: Session = Depends(get_db)
):
    """Получить абсолютные остатки по SKU (сумма со всех локаций)"""
    query = db.query(InventorySKUTotal)
    
    if sku_id:
        query = query.filter(InventorySKUTotal.sku_id == sku_id)
    
    query = query.order_by(InventorySKUTotal.sku_name)
    
    totals = query.offset(skip).limit(limit).all()
    return totals


@router.get("/locations", response_model=List[LocationTotalResponse])
async def get_location_totals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_name: Optional[str] = Query(None, description="Фильтр по названию локации"),
    sku_id: Optional[int] = Query(None, description="Фильтр по ID товара"),
    db: Session = Depends(get_db)
):
    """Получить остатки по локациям"""
    query = db.query(InventoryLocationTotal)
    
    if location_name:
        query = query.filter(InventoryLocationTotal.location_name == location_name)
    
    if sku_id:
        query = query.filter(InventoryLocationTotal.sku_id == sku_id)
    
    query = query.order_by(InventoryLocationTotal.location_name, InventoryLocationTotal.sku_name)
    
    totals = query.offset(skip).limit(limit).all()
    return totals


@router.get("/locations/{location_name}", response_model=List[LocationTotalResponse])
async def get_location_totals_by_location(
    location_name: str,
    db: Session = Depends(get_db)
):
    """Получить остатки товаров в конкретной локации"""
    totals = db.query(InventoryLocationTotal).filter(
        InventoryLocationTotal.location_name == location_name
    ).order_by(InventoryLocationTotal.sku_name).all()
    
    return totals


@router.get("/sku/{sku_id}/history", response_model=List[OperationResponse])
async def get_sku_history(
    sku_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Получить историю операций по конкретному товару"""
    operations = db.query(InventoryOperation).filter(
        InventoryOperation.sku_id == sku_id
    ).order_by(InventoryOperation.created_at.desc()).offset(skip).limit(limit).all()
    
    return operations

