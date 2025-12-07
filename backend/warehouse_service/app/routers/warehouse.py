from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging

from app.database import get_db
from app.models import Location, WarehouseOperation, TempStorageItem
from app.schemas import (
    LocationResponse, LocationStatsResponse, WarehouseOperationCreate,
    WarehouseOperationResponse, TempStorageItemResponse
)
from app.warehouse_service import WarehouseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/warehouse", tags=["warehouse"])


@router.get("/locations/stats", response_model=List[LocationStatsResponse])
async def get_locations_stats(db: Session = Depends(get_db)):
    """Получить статистику по всем локациям"""
    stats = await WarehouseService.get_location_stats(db)
    return stats


@router.get("/locations", response_model=List[LocationResponse])
async def get_locations(db: Session = Depends(get_db)):
    """Получить все локации"""
    locations = db.query(Location).all()
    return locations


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(location_id: int, db: Session = Depends(get_db)):
    """Получить локацию по ID"""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    return location


@router.post("/operations", response_model=WarehouseOperationResponse, status_code=201)
async def create_operation(
    operation: WarehouseOperationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Создать операцию перемещения товаров"""
    # Создаем запись операции
    db_operation = WarehouseOperation(
        operation_type=operation.operation_type,
        sku_id=operation.sku_id,
        source_location_id=operation.source_location_id,
        target_location_id=operation.target_location_id,
        quantity_kg=0,  # Будет рассчитано при обработке
        status="pending"
    )
    
    # Получаем название товара если указан ID
    if operation.sku_id:
        try:
            from app.catalog_client import catalog_client
            sku_info = await catalog_client.get_sku(operation.sku_id)
            if sku_info:
                db_operation.sku_name = sku_info.get('name', 'Unknown')
        except Exception as e:
            logger.warning(f"Не удалось получить информацию о товаре {operation.sku_id}: {e}")
            db_operation.sku_name = f"SKU_{operation.sku_id}"
    
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    
    # Обрабатываем операцию в фоне
    background_tasks.add_task(process_operation_background, db_operation.id)
    
    return db_operation


async def process_operation_background(operation_id: int):
    """Фоновая обработка операции"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        operation = db.query(WarehouseOperation).filter(WarehouseOperation.id == operation_id).first()
        if not operation:
            logger.error(f"Операция {operation_id} не найдена")
            return
        
        success, error_message = await WarehouseService.process_operation(db, operation)
        
        if success:
            operation.status = "completed"
            operation.completed_at = datetime.now()
            if error_message:
                operation.error_message = error_message  # Предупреждения о недостатке места
        else:
            operation.status = "failed"
            operation.error_message = error_message
        
        db.commit()
        logger.info(f"Операция {operation_id} обработана: {operation.status}")
    except Exception as e:
        logger.error(f"Ошибка при обработке операции {operation_id}: {e}")
        try:
            operation = db.query(WarehouseOperation).filter(WarehouseOperation.id == operation_id).first()
            if operation:
                operation.status = "failed"
                operation.error_message = str(e)
                db.commit()
        except:
            pass
    finally:
        db.close()


@router.get("/operations", response_model=List[WarehouseOperationResponse])
async def get_operations(db: Session = Depends(get_db)):
    """Получить все операции"""
    operations = db.query(WarehouseOperation).order_by(WarehouseOperation.created_at.desc()).all()
    return operations


@router.get("/operations/{operation_id}", response_model=WarehouseOperationResponse)
async def get_operation(operation_id: int, db: Session = Depends(get_db)):
    """Получить операцию по ID"""
    operation = db.query(WarehouseOperation).filter(WarehouseOperation.id == operation_id).first()
    if not operation:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    return operation


@router.get("/temp-storage", response_model=List[TempStorageItemResponse])
async def get_temp_storage_items(db: Session = Depends(get_db)):
    """Получить все элементы временного хранилища"""
    items = db.query(TempStorageItem).filter(
        TempStorageItem.moved_to_storage_at.is_(None)
    ).order_by(TempStorageItem.created_at).all()
    return items


@router.post("/temp-storage/process")
async def process_temp_storage(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Обработать перемещение товаров из временного хранилища в основное"""
    background_tasks.add_task(WarehouseService.process_temp_storage_migration, db)
    return {"message": "Обработка временного хранилища запущена"}

