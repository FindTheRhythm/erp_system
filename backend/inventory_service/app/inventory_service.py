"""
Сервисная логика для работы с остатками и операциями
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from app.models import InventoryOperation, InventorySKUTotal, InventoryLocationTotal
from app.catalog_client import catalog_client

logger = logging.getLogger(__name__)


class InventoryService:
    """Сервис для работы с остатками и операциями"""
    
    @staticmethod
    async def calculate_delta_value(
        quantity_value: int,
        quantity_unit_name: str,
        weight_value: float,
        weight_unit_name: str
    ) -> int:
        """
        Рассчитать итоговое значение (delta_value) = количество * коэффициент_количества * вес * коэффициент_веса
        
        Args:
            quantity_value: Значение количества
            quantity_unit_name: Название единицы количества (шт/уп/ящ/пал)
            weight_value: Значение веса
            weight_unit_name: Название единицы веса (т/кг/г)
        
        Returns:
            Итоговое значение в килограммах
        """
        # Получаем коэффициенты для единиц измерения из Catalog Service
        quantity_coefficient = await catalog_client.get_quantity_unit_coefficient(quantity_unit_name)
        weight_coefficient = await catalog_client.get_weight_unit_coefficient(weight_unit_name)
        
        # Рассчитываем итоговое значение: количество * коэффициент_количества * вес * коэффициент_веса
        delta_value = int(quantity_value * quantity_coefficient * weight_value * weight_coefficient)
        
        return delta_value
    
    @staticmethod
    async def create_operation(
        db: Session,
        operation_type: str,
        sku_id: int,
        quantity_value: int,
        quantity_unit: str,
        weight_value: int,
        weight_unit: str,
        source_location: Optional[str] = None,
        target_location: Optional[str] = None
    ) -> InventoryOperation:
        """
        Создать операцию и обновить остатки
        
        Args:
            db: Сессия БД
            operation_type: Тип операции
            sku_id: ID товара
            quantity_value: Значение количества
            quantity_unit: Единица количества
            weight_value: Значение веса
            weight_unit: Единица веса
            source_location: Начальная локация
            target_location: Конечная локация
        
        Returns:
            Созданная операция
        """
        # Получаем информацию о товаре из Catalog Service
        sku_info = await catalog_client.get_sku(sku_id)
        if not sku_info:
            raise ValueError(f"SKU {sku_id} not found in Catalog Service")
        
        sku_name = sku_info.get('name', 'Unknown')
        
        # Рассчитываем итоговое значение используя названия единиц измерения
        # Конвертируем weight_value в float для точного расчета
        delta_value = await InventoryService.calculate_delta_value(
            quantity_value,
            quantity_unit,
            float(weight_value),
            weight_unit
        )
        
        # Если одна локация, то target = source
        if operation_type != 'transfer':
            target_location = source_location
        
        # Создаем операцию
        operation = InventoryOperation(
            operation_type=operation_type,
            sku_id=sku_id,
            sku_name=sku_name,
            quantity_value=quantity_value,
            quantity_unit=quantity_unit,
            weight_value=weight_value,
            weight_unit=weight_unit,
            delta_value=delta_value,  # Храним абсолютное значение, знак определяем при обновлении остатков
            delta_unit="кг",
            source_location=source_location,
            target_location=target_location
        )
        
        db.add(operation)
        db.flush()  # Получаем ID операции
        
        # Обновляем остатки
        await InventoryService._update_totals(
            db,
            sku_id,
            sku_name,
            operation_type,
            delta_value,
            source_location,
            target_location
        )
        
        db.commit()
        db.refresh(operation)
        
        logger.info(f"Created operation {operation.id} of type {operation_type} for SKU {sku_id}")
        
        return operation
    
    @staticmethod
    async def create_operation_with_delta(
        db: Session,
        operation_type: str,
        sku_id: int,
        quantity_value: int,
        quantity_unit: str,
        weight_value: int,
        weight_unit: str,
        delta_value: int,
        source_location: Optional[str] = None,
        target_location: Optional[str] = None
    ) -> InventoryOperation:
        """
        Создать операцию с заданным delta_value (для операций delete)
        """
        # Получаем информацию о товаре из Catalog Service или из остатков
        sku_name = 'Unknown'
        sku_info = await catalog_client.get_sku(sku_id)
        if sku_info:
            sku_name = sku_info.get('name', 'Unknown')
        else:
            # Если товар уже удален из Catalog, берем имя из остатков
            sku_total = db.query(InventorySKUTotal).filter(InventorySKUTotal.sku_id == sku_id).first()
            if sku_total:
                sku_name = sku_total.sku_name
        
        # Если одна локация, то target = source
        if operation_type != 'transfer':
            target_location = source_location
        
        # Создаем операцию
        operation = InventoryOperation(
            operation_type=operation_type,
            sku_id=sku_id,
            sku_name=sku_name,
            quantity_value=quantity_value,
            quantity_unit=quantity_unit,
            weight_value=weight_value,
            weight_unit=weight_unit,
            delta_value=delta_value,  # Используем переданное значение
            delta_unit="кг",
            source_location=source_location,
            target_location=target_location
        )
        
        db.add(operation)
        db.flush()  # Получаем ID операции
        
        # Обновляем остатки
        # Для delete используем абсолютное значение delta_value (оно уже отрицательное)
        await InventoryService._update_totals(
            db,
            sku_id,
            sku_name,
            operation_type,
            abs(delta_value),  # Передаем абсолютное значение для обновления остатков
            source_location,
            target_location
        )
        
        db.commit()
        db.refresh(operation)
        
        logger.info(f"Created operation {operation.id} of type {operation_type} for SKU {sku_id} with delta_value {delta_value}")
        
        return operation
    
    @staticmethod
    async def _update_totals(
        db: Session,
        sku_id: int,
        sku_name: str,
        operation_type: str,
        delta_value: int,
        source_location: Optional[str],
        target_location: Optional[str]
    ):
        """
        Обновить остатки после операции
        
        Args:
            db: Сессия БД
            sku_id: ID товара
            sku_name: Название товара
            operation_type: Тип операции
            delta_value: Изменение значения (в кг)
            source_location: Начальная локация
            target_location: Конечная локация
        """
        if operation_type == 'transfer':
            # Перемещение: уменьшаем в source, увеличиваем в target
            InventoryService._update_location_total(db, sku_id, sku_name, source_location, -delta_value)
            InventoryService._update_location_total(db, sku_id, sku_name, target_location, delta_value)
            # Абсолютные остатки не меняются при перемещении
        elif operation_type in ['receipt', 'create']:
            # Прием/создание: увеличиваем остатки
            InventoryService._update_location_total(db, sku_id, sku_name, source_location, delta_value)
            InventoryService._update_sku_total(db, sku_id, sku_name, delta_value)
        elif operation_type in ['write_off', 'delete']:
            # Списание/удаление: уменьшаем остатки
            InventoryService._update_location_total(db, sku_id, sku_name, source_location, -delta_value)
            InventoryService._update_sku_total(db, sku_id, sku_name, -delta_value)
        elif operation_type == 'update':
            # Изменение товара: обновляем остатки на новое значение
            # Находим существующую запись и обновляем её
            sku_total = db.query(InventorySKUTotal).filter(InventorySKUTotal.sku_id == sku_id).first()
            if sku_total:
                # Обновляем абсолютные остатки
                sku_total.total_weight = delta_value
                sku_total.sku_name = sku_name
            else:
                # Если записи нет, создаем новую
                InventoryService._update_sku_total(db, sku_id, sku_name, delta_value)
            
            # Обновляем остатки по локациям
            if source_location:
                location_total = db.query(InventoryLocationTotal).filter(
                    and_(
                        InventoryLocationTotal.sku_id == sku_id,
                        InventoryLocationTotal.location_name == source_location
                    )
                ).first()
                
                if location_total:
                    location_total.weight = delta_value
                    location_total.sku_name = sku_name
                else:
                    # Если записи нет, создаем новую
                    InventoryService._update_location_total(db, sku_id, sku_name, source_location, delta_value)
    
    @staticmethod
    def _update_sku_total(db: Session, sku_id: int, sku_name: str, delta_weight: int):
        """Обновить абсолютные остатки по SKU"""
        sku_total = db.query(InventorySKUTotal).filter(InventorySKUTotal.sku_id == sku_id).first()
        
        if sku_total:
            sku_total.total_weight += delta_weight
            sku_total.sku_name = sku_name  # Обновляем название на случай изменения
        else:
            # Создаем новую запись
            sku_total = InventorySKUTotal(
                sku_id=sku_id,
                sku_name=sku_name,
                total_weight=delta_weight,
                total_quantity=0  # Количество не отслеживаем в абсолютных остатках
            )
            db.add(sku_total)
    
    @staticmethod
    def _update_location_total(db: Session, sku_id: int, sku_name: str, location_name: Optional[str], delta_weight: int):
        """Обновить остатки по локации"""
        if not location_name:
            return
        
        location_total = db.query(InventoryLocationTotal).filter(
            and_(
                InventoryLocationTotal.sku_id == sku_id,
                InventoryLocationTotal.location_name == location_name
            )
        ).first()
        
        if location_total:
            location_total.weight += delta_weight
            location_total.sku_name = sku_name  # Обновляем название на случай изменения
        else:
            # Создаем новую запись
            location_total = InventoryLocationTotal(
                sku_id=sku_id,
                sku_name=sku_name,
                location_name=location_name,
                weight=delta_weight,
                quantity=0  # Количество не отслеживаем в остатках по локациям
            )
            db.add(location_total)

