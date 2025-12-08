"""
Сервисная логика для работы со складами и операциями
"""
import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Tuple
from app.models import Location, WarehouseOperation, TempStorageItem, LocationType, OperationType
from app.inventory_client import inventory_client
from app.catalog_client import catalog_client
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WarehouseService:
    """Сервис для работы со складами и операциями"""
    
    @staticmethod
    async def get_location_stats(db: Session) -> List[Dict]:
        """Получить статистику по всем локациям (синхронизирует с Inventory Service)"""
        try:
            locations = db.query(Location).all()
            stats = []
            
            for location in locations:
                # Получаем реальные остатки из Inventory Service
                try:
                    location_totals = await inventory_client.get_location_totals(location.name)
                    current_weight = sum(item.get('weight', 0) for item in location_totals if isinstance(item, dict))
                except Exception as e:
                    # Если не удалось получить данные из Inventory Service, используем значение из БД
                    logger.warning(f"Не удалось получить остатки для локации {location.name}: {e}")
                    current_weight = location.current_capacity_kg or 0
                
                # Обновляем current_capacity_kg в БД только если значение изменилось
                if location.current_capacity_kg != current_weight:
                    location.current_capacity_kg = current_weight
                
                usage_percent = (current_weight / location.max_capacity_kg * 100) if location.max_capacity_kg > 0 else 0
                
                stats.append({
                    "id": location.id,
                    "name": location.name,
                    "type": location.type.value,
                    "max_capacity_kg": location.max_capacity_kg,
                    "current_capacity_kg": current_weight,
                    "usage_percent": round(usage_percent, 2),
                    "description": location.description
                })
            
            # Коммитим все изменения одним разом (если есть изменения)
            try:
                db.commit()
            except Exception as commit_error:
                logger.warning(f"Ошибка при коммите изменений: {commit_error}")
                db.rollback()
            
            return stats
        except Exception as e:
            logger.error(f"Критическая ошибка в get_location_stats: {e}", exc_info=True)
            db.rollback()
            # Возвращаем пустой список вместо исключения
            return []
    
    @staticmethod
    async def update_location_capacity(db: Session, location_id: int, delta_kg: int):
        """Обновить заполненность локации"""
        location = db.query(Location).filter(Location.id == location_id).first()
        if location:
            location.current_capacity_kg = max(0, location.current_capacity_kg + delta_kg)
            db.commit()
    
    @staticmethod
    async def check_capacity(db: Session, location_id: int, required_kg: int) -> Tuple[bool, int]:
        """
        Проверить, есть ли место в локации
        
        Returns:
            (достаточно места, доступное место в кг)
        """
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return False, 0
        
        available = location.max_capacity_kg - location.current_capacity_kg
        return available >= required_kg, available
    
    @staticmethod
    async def get_location_by_name(db: Session, name: str) -> Optional[Location]:
        """Получить локацию по имени"""
        return db.query(Location).filter(Location.name == name).first()
    
    @staticmethod
    async def get_temp_storage_location(db: Session) -> Optional[Location]:
        """Получить или создать временное хранилище"""
        temp_storage = db.query(Location).filter(Location.type == LocationType.TEMP_STORAGE).first()
        if not temp_storage:
            # Создаем временное хранилище с большим объемом
            temp_storage = Location(
                name="Временное хранилище",
                type=LocationType.TEMP_STORAGE,
                max_capacity_kg=1000000,  # Большой объем для временного хранения
                current_capacity_kg=0,
                description="Временное хранилище для излишков товаров"
            )
            db.add(temp_storage)
            db.commit()
            db.refresh(temp_storage)
        return temp_storage
    
    @staticmethod
    async def get_main_storage_location(db: Session) -> Optional[Location]:
        """Получить основное хранилище"""
        return db.query(Location).filter(Location.name == "Материнское хранилище").first()
    
    @staticmethod
    async def get_warehouse_locations(db: Session) -> List[Location]:
        """Получить все склады (не хранилища)"""
        return db.query(Location).filter(Location.type == LocationType.WAREHOUSE).all()
    
    @staticmethod
    async def process_operation(
        db: Session,
        operation: WarehouseOperation
    ) -> Tuple[bool, Optional[str]]:
        """
        Обработать операцию перемещения
        
        Returns:
            (успех, сообщение об ошибке)
        """
        try:
            if operation.operation_type == OperationType.RECEIPT:
                return await WarehouseService._process_receipt(db, operation)
            elif operation.operation_type == OperationType.SHIPMENT:
                return await WarehouseService._process_shipment(db, operation)
            elif operation.operation_type == OperationType.TRANSFER:
                return await WarehouseService._process_transfer(db, operation)
            elif operation.operation_type == OperationType.GLOBAL_DISTRIBUTION_ALL:
                return await WarehouseService._process_global_distribution_all(db, operation)
            elif operation.operation_type == OperationType.GLOBAL_DISTRIBUTION_SKU:
                return await WarehouseService._process_global_distribution_sku(db, operation)
            elif operation.operation_type == OperationType.REPLENISHMENT_ALL:
                return await WarehouseService._process_replenishment_all(db, operation)
            elif operation.operation_type == OperationType.REPLENISHMENT_SKU:
                return await WarehouseService._process_replenishment_sku(db, operation)
            elif operation.operation_type == OperationType.PLACEMENT_ALL:
                return await WarehouseService._process_placement_all(db, operation)
            elif operation.operation_type == OperationType.PLACEMENT_SKU:
                return await WarehouseService._process_placement_sku(db, operation)
            else:
                return False, f"Неизвестный тип операции: {operation.operation_type}"
        except Exception as e:
            logger.error(f"Error processing operation {operation.id}: {e}")
            return False, str(e)
    
    @staticmethod
    async def _process_receipt(db: Session, operation: WarehouseOperation) -> Tuple[bool, Optional[str]]:
        """Прием товара складом из хранилища"""
        if not operation.sku_id or not operation.source_location_id or not operation.target_location_id:
            return False, "Не указаны обязательные параметры"
        
        # Получаем остатки товара в исходной локации
        source_location = db.query(Location).filter(Location.id == operation.source_location_id).first()
        if not source_location:
            return False, "Исходная локация не найдена"
        
        target_location = db.query(Location).filter(Location.id == operation.target_location_id).first()
        if not target_location:
            return False, "Целевая локация не найдена"
        
        # Получаем остатки из Inventory Service
        location_totals = await inventory_client.get_location_totals(source_location.name)
        sku_total = next((item for item in location_totals if item['sku_id'] == operation.sku_id), None)
        
        if not sku_total or sku_total['weight'] <= 0:
            return False, f"Товар {operation.sku_name} отсутствует в {source_location.name}"
        
        available_weight = sku_total['weight']
        requested_weight = operation.quantity_kg
        
        # Проверяем доступное количество
        transfer_weight = min(available_weight, requested_weight)
        
        # Проверяем место в целевой локации
        has_space, available_space = await WarehouseService.check_capacity(db, operation.target_location_id, transfer_weight)
        
        if not has_space:
            # Излишки отправляем во временное хранилище
            excess = transfer_weight - available_space
            transfer_weight = available_space
            
            # Перемещаем излишки во временное хранилище
            temp_storage = await WarehouseService.get_temp_storage_location(db)
            if temp_storage:
                await WarehouseService._move_to_temp_storage(db, operation.sku_id, operation.sku_name, excess, operation.id)
        
        # Выполняем перемещение через Inventory Service
        if transfer_weight > 0:
            success = await inventory_client.create_operation(
                operation_type="transfer",
                sku_id=operation.sku_id,
                quantity_value=1,  # Будет пересчитано в Inventory Service
                quantity_unit="шт",
                weight_value=transfer_weight,
                weight_unit="кг",
                source_location=source_location.name,
                target_location=target_location.name
            )
            
            if success:
                await WarehouseService.update_location_capacity(db, operation.source_location_id, -transfer_weight)
                await WarehouseService.update_location_capacity(db, operation.target_location_id, transfer_weight)
                return True, None
            else:
                return False, "Ошибка при создании операции в Inventory Service"
        
        return False, "Не удалось выполнить перемещение"
    
    @staticmethod
    async def _process_shipment(db: Session, operation: WarehouseOperation) -> Tuple[bool, Optional[str]]:
        """Отгрузка товара со склада в хранилище"""
        # Аналогично receipt, но в обратном направлении
        return await WarehouseService._process_receipt(db, operation)
    
    @staticmethod
    async def _process_transfer(db: Session, operation: WarehouseOperation) -> Tuple[bool, Optional[str]]:
        """Перемещение между складами"""
        return await WarehouseService._process_receipt(db, operation)
    
    @staticmethod
    async def _move_to_temp_storage(
        db: Session,
        sku_id: int,
        sku_name: str,
        quantity_kg: int,
        source_operation_id: Optional[int] = None
    ):
        """Переместить товар во временное хранилище"""
        temp_storage = await WarehouseService.get_temp_storage_location(db)
        if not temp_storage:
            logger.error("Не удалось получить временное хранилище")
            return
        
        temp_item = TempStorageItem(
            sku_id=sku_id,
            sku_name=sku_name,
            quantity_kg=quantity_kg,
            source_operation_id=source_operation_id
        )
        db.add(temp_item)
        await WarehouseService.update_location_capacity(db, temp_storage.id, quantity_kg)
        db.commit()
    
    @staticmethod
    async def _process_global_distribution_all(db: Session, operation: WarehouseOperation) -> Tuple[bool, Optional[str]]:
        """Глобальное распределение (все товары) - равномерно по 4 складам"""
        warehouses = await WarehouseService.get_warehouse_locations(db)
        if len(warehouses) != 4:
            return False, "Должно быть ровно 4 склада"
        
        # Получаем все товары из хранилища
        main_storage = await WarehouseService.get_main_storage_location(db)
        if not main_storage:
            return False, "Основное хранилище не найдено"
        
        location_totals = await inventory_client.get_location_totals(main_storage.name)
        
        errors = []
        for item in location_totals:
            if item['weight'] > 0:
                # Распределяем равномерно по 4 складам
                weight_per_warehouse = item['weight'] // 4
                remainder = item['weight'] % 4
                
                for i, warehouse in enumerate(warehouses):
                    transfer_weight = weight_per_warehouse + (1 if i < remainder else 0)
                    
                    if transfer_weight > 0:
                        has_space, available_space = await WarehouseService.check_capacity(db, warehouse.id, transfer_weight)
                        
                        if has_space:
                            success = await inventory_client.create_operation(
                                operation_type="transfer",
                                sku_id=item['sku_id'],
                                quantity_value=1,
                                quantity_unit="шт",
                                weight_value=transfer_weight,
                                weight_unit="кг",
                                source_location=main_storage.name,
                                target_location=warehouse.name
                            )
                            
                            if success:
                                await WarehouseService.update_location_capacity(db, main_storage.id, -transfer_weight)
                                await WarehouseService.update_location_capacity(db, warehouse.id, transfer_weight)
                        else:
                            # Излишки во временное хранилище
                            excess = transfer_weight - available_space
                            if available_space > 0:
                                success = await inventory_client.create_operation(
                                    operation_type="transfer",
                                    sku_id=item['sku_id'],
                                    quantity_value=1,
                                    quantity_unit="шт",
                                    weight_value=available_space,
                                    weight_unit="кг",
                                    source_location=main_storage.name,
                                    target_location=warehouse.name
                                )
                                if success:
                                    await WarehouseService.update_location_capacity(db, main_storage.id, -available_space)
                                    await WarehouseService.update_location_capacity(db, warehouse.id, available_space)
                            
                            await WarehouseService._move_to_temp_storage(db, item['sku_id'], item['sku_name'], excess, operation.id)
                            errors.append(f"Недостаточно места в {warehouse.name} для товара {item['sku_name']}")
        
        if errors:
            return True, "; ".join(errors)
        return True, None
    
    @staticmethod
    async def _process_global_distribution_sku(db: Session, operation: WarehouseOperation) -> Tuple[bool, Optional[str]]:
        """Глобальное распределение (товар) - выбранный товар равномерно по 4 складам"""
        if not operation.sku_id:
            return False, "Не указан ID товара"
        
        warehouses = await WarehouseService.get_warehouse_locations(db)
        if len(warehouses) != 4:
            return False, "Должно быть ровно 4 склада"
        
        main_storage = await WarehouseService.get_main_storage_location(db)
        if not main_storage:
            return False, "Основное хранилище не найдено"
        
        location_totals = await inventory_client.get_location_totals(main_storage.name)
        sku_total = next((item for item in location_totals if item['sku_id'] == operation.sku_id), None)
        
        if not sku_total or sku_total['weight'] <= 0:
            return False, f"Товар {operation.sku_name} отсутствует в хранилище"
        
        weight_per_warehouse = sku_total['weight'] // 4
        remainder = sku_total['weight'] % 4
        
        errors = []
        for i, warehouse in enumerate(warehouses):
            transfer_weight = weight_per_warehouse + (1 if i < remainder else 0)
            
            if transfer_weight > 0:
                has_space, available_space = await WarehouseService.check_capacity(db, warehouse.id, transfer_weight)
                
                if has_space:
                    success = await inventory_client.create_operation(
                        operation_type="transfer",
                        sku_id=operation.sku_id,
                        quantity_value=1,
                        quantity_unit="шт",
                        weight_value=transfer_weight,
                        weight_unit="кг",
                        source_location=main_storage.name,
                        target_location=warehouse.name
                    )
                    
                    if success:
                        await WarehouseService.update_location_capacity(db, main_storage.id, -transfer_weight)
                        await WarehouseService.update_location_capacity(db, warehouse.id, transfer_weight)
                else:
                    excess = transfer_weight - available_space
                    if available_space > 0:
                        success = await inventory_client.create_operation(
                            operation_type="transfer",
                            sku_id=operation.sku_id,
                            quantity_value=1,
                            quantity_unit="шт",
                            weight_value=available_space,
                            weight_unit="кг",
                            source_location=main_storage.name,
                            target_location=warehouse.name
                        )
                        if success:
                            await WarehouseService.update_location_capacity(db, main_storage.id, -available_space)
                            await WarehouseService.update_location_capacity(db, warehouse.id, available_space)
                    
                    await WarehouseService._move_to_temp_storage(db, operation.sku_id, operation.sku_name, excess, operation.id)
                    errors.append(f"Недостаточно места в {warehouse.name}")
        
        if errors:
            return True, "; ".join(errors)
        return True, None
    
    @staticmethod
    async def _process_replenishment_all(db: Session, operation: WarehouseOperation) -> Tuple[bool, Optional[str]]:
        """Пополнение запасов (все товары) - в выбранный склад со всех складов"""
        if not operation.target_location_id:
            return False, "Не указан целевой склад"
        
        target_location = db.query(Location).filter(Location.id == operation.target_location_id).first()
        if not target_location:
            return False, "Целевой склад не найден"
        
        # Получаем все склады кроме целевого
        warehouses = await WarehouseService.get_warehouse_locations(db)
        source_warehouses = [w for w in warehouses if w.id != operation.target_location_id]
        
        errors = []
        for warehouse in source_warehouses:
            location_totals = await inventory_client.get_location_totals(warehouse.name)
            
            for item in location_totals:
                if item['weight'] > 0:
                    has_space, available_space = await WarehouseService.check_capacity(db, operation.target_location_id, item['weight'])
                    
                    if has_space:
                        success = await inventory_client.create_operation(
                            operation_type="transfer",
                            sku_id=item['sku_id'],
                            quantity_value=1,
                            quantity_unit="шт",
                            weight_value=item['weight'],
                            weight_unit="кг",
                            source_location=warehouse.name,
                            target_location=target_location.name
                        )
                        
                        if success:
                            await WarehouseService.update_location_capacity(db, warehouse.id, -item['weight'])
                            await WarehouseService.update_location_capacity(db, operation.target_location_id, item['weight'])
                    else:
                        excess = item['weight'] - available_space
                        if available_space > 0:
                            success = await inventory_client.create_operation(
                                operation_type="transfer",
                                sku_id=item['sku_id'],
                                quantity_value=1,
                                quantity_unit="шт",
                                weight_value=available_space,
                                weight_unit="кг",
                                source_location=warehouse.name,
                                target_location=target_location.name
                            )
                            if success:
                                await WarehouseService.update_location_capacity(db, warehouse.id, -available_space)
                                await WarehouseService.update_location_capacity(db, operation.target_location_id, available_space)
                        
                        await WarehouseService._move_to_temp_storage(db, item['sku_id'], item['sku_name'], excess, operation.id)
                        errors.append(f"Недостаточно места в {target_location.name} для товара {item['sku_name']}")
        
        if errors:
            return True, "; ".join(errors)
        return True, None
    
    @staticmethod
    async def _process_replenishment_sku(db: Session, operation: WarehouseOperation) -> Tuple[bool, Optional[str]]:
        """Пополнение запасов (товар) - в выбранный склад выбранный товар со всех локаций"""
        if not operation.sku_id or not operation.target_location_id:
            return False, "Не указаны обязательные параметры"
        
        target_location = db.query(Location).filter(Location.id == operation.target_location_id).first()
        if not target_location:
            return False, "Целевой склад не найден"
        
        # Получаем все локации кроме целевой
        all_locations = db.query(Location).filter(Location.id != operation.target_location_id).all()
        
        total_weight = 0
        for location in all_locations:
            location_totals = await inventory_client.get_location_totals(location.name)
            sku_total = next((item for item in location_totals if item['sku_id'] == operation.sku_id), None)
            if sku_total:
                total_weight += sku_total['weight']
        
        if total_weight == 0:
            return False, f"Товар {operation.sku_name} отсутствует в других локациях"
        
        has_space, available_space = await WarehouseService.check_capacity(db, operation.target_location_id, total_weight)
        
        errors = []
        transfer_weight = min(total_weight, available_space) if has_space else available_space
        
        # Перемещаем из всех локаций
        moved_weight = 0
        for location in all_locations:
            if moved_weight >= transfer_weight:
                break
            
            location_totals = await inventory_client.get_location_totals(location.name)
            sku_total = next((item for item in location_totals if item['sku_id'] == operation.sku_id), None)
            
            if sku_total and sku_total['weight'] > 0:
                move_weight = min(sku_total['weight'], transfer_weight - moved_weight)
                
                success = await inventory_client.create_operation(
                    operation_type="transfer",
                    sku_id=operation.sku_id,
                    quantity_value=1,
                    quantity_unit="шт",
                    weight_value=move_weight,
                    weight_unit="кг",
                    source_location=location.name,
                    target_location=target_location.name
                )
                
                if success:
                    await WarehouseService.update_location_capacity(db, location.id, -move_weight)
                    await WarehouseService.update_location_capacity(db, operation.target_location_id, move_weight)
                    moved_weight += move_weight
        
        # Излишки во временное хранилище
        if total_weight > transfer_weight:
            excess = total_weight - transfer_weight
            await WarehouseService._move_to_temp_storage(db, operation.sku_id, operation.sku_name, excess, operation.id)
            errors.append(f"Недостаточно места в {target_location.name}, {excess} кг отправлено во временное хранилище")
        
        if errors:
            return True, "; ".join(errors)
        return True, None
    
    @staticmethod
    async def _process_placement_all(db: Session, operation: WarehouseOperation) -> Tuple[bool, Optional[str]]:
        """Размещение запасов (все товары) - из выбранного склада равномерно по остальным 3 складам"""
        if not operation.source_location_id:
            return False, "Не указан исходный склад"
        
        source_location = db.query(Location).filter(Location.id == operation.source_location_id).first()
        if not source_location:
            return False, "Исходный склад не найден"
        
        warehouses = await WarehouseService.get_warehouse_locations(db)
        target_warehouses = [w for w in warehouses if w.id != operation.source_location_id]
        
        if len(target_warehouses) != 3:
            return False, "Должно быть ровно 3 целевых склада"
        
        location_totals = await inventory_client.get_location_totals(source_location.name)
        
        errors = []
        for item in location_totals:
            if item['weight'] > 0:
                weight_per_warehouse = item['weight'] // 3
                remainder = item['weight'] % 3
                
                for i, warehouse in enumerate(target_warehouses):
                    transfer_weight = weight_per_warehouse + (1 if i < remainder else 0)
                    
                    if transfer_weight > 0:
                        has_space, available_space = await WarehouseService.check_capacity(db, warehouse.id, transfer_weight)
                        
                        if has_space:
                            success = await inventory_client.create_operation(
                                operation_type="transfer",
                                sku_id=item['sku_id'],
                                quantity_value=1,
                                quantity_unit="шт",
                                weight_value=transfer_weight,
                                weight_unit="кг",
                                source_location=source_location.name,
                                target_location=warehouse.name
                            )
                            
                            if success:
                                await WarehouseService.update_location_capacity(db, source_location.id, -transfer_weight)
                                await WarehouseService.update_location_capacity(db, warehouse.id, transfer_weight)
                        else:
                            excess = transfer_weight - available_space
                            if available_space > 0:
                                success = await inventory_client.create_operation(
                                    operation_type="transfer",
                                    sku_id=item['sku_id'],
                                    quantity_value=1,
                                    quantity_unit="шт",
                                    weight_value=available_space,
                                    weight_unit="кг",
                                    source_location=source_location.name,
                                    target_location=warehouse.name
                                )
                                if success:
                                    await WarehouseService.update_location_capacity(db, source_location.id, -available_space)
                                    await WarehouseService.update_location_capacity(db, warehouse.id, available_space)
                            
                            await WarehouseService._move_to_temp_storage(db, item['sku_id'], item['sku_name'], excess, operation.id)
                            errors.append(f"Недостаточно места в {warehouse.name} для товара {item['sku_name']}")
        
        if errors:
            return True, "; ".join(errors)
        return True, None
    
    @staticmethod
    async def _process_placement_sku(db: Session, operation: WarehouseOperation) -> Tuple[bool, Optional[str]]:
        """Размещение запасов (товар) - выбранный товар из выбранного склада равномерно по остальным 3 складам"""
        if not operation.sku_id or not operation.source_location_id:
            return False, "Не указаны обязательные параметры"
        
        source_location = db.query(Location).filter(Location.id == operation.source_location_id).first()
        if not source_location:
            return False, "Исходный склад не найден"
        
        warehouses = await WarehouseService.get_warehouse_locations(db)
        target_warehouses = [w for w in warehouses if w.id != operation.source_location_id]
        
        if len(target_warehouses) != 3:
            return False, "Должно быть ровно 3 целевых склада"
        
        location_totals = await inventory_client.get_location_totals(source_location.name)
        sku_total = next((item for item in location_totals if item['sku_id'] == operation.sku_id), None)
        
        if not sku_total or sku_total['weight'] <= 0:
            return False, f"Товар {operation.sku_name} отсутствует в {source_location.name}"
        
        weight_per_warehouse = sku_total['weight'] // 3
        remainder = sku_total['weight'] % 3
        
        errors = []
        for i, warehouse in enumerate(target_warehouses):
            transfer_weight = weight_per_warehouse + (1 if i < remainder else 0)
            
            if transfer_weight > 0:
                has_space, available_space = await WarehouseService.check_capacity(db, warehouse.id, transfer_weight)
                
                if has_space:
                    success = await inventory_client.create_operation(
                        operation_type="transfer",
                        sku_id=operation.sku_id,
                        quantity_value=1,
                        quantity_unit="шт",
                        weight_value=transfer_weight,
                        weight_unit="кг",
                        source_location=source_location.name,
                        target_location=warehouse.name
                    )
                    
                    if success:
                        await WarehouseService.update_location_capacity(db, source_location.id, -transfer_weight)
                        await WarehouseService.update_location_capacity(db, warehouse.id, transfer_weight)
                else:
                    excess = transfer_weight - available_space
                    if available_space > 0:
                        success = await inventory_client.create_operation(
                            operation_type="transfer",
                            sku_id=operation.sku_id,
                            quantity_value=1,
                            quantity_unit="шт",
                            weight_value=available_space,
                            weight_unit="кг",
                            source_location=source_location.name,
                            target_location=warehouse.name
                        )
                        if success:
                            await WarehouseService.update_location_capacity(db, source_location.id, -available_space)
                            await WarehouseService.update_location_capacity(db, warehouse.id, available_space)
                    
                    await WarehouseService._move_to_temp_storage(db, operation.sku_id, operation.sku_name, excess, operation.id)
                    errors.append(f"Недостаточно места в {warehouse.name}")
        
        if errors:
            return True, "; ".join(errors)
        return True, None
    
    @staticmethod
    async def process_temp_storage_migration(db: Session):
        """Обработать перемещение товаров из временного хранилища в основное (через 5 минут)"""
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        
        temp_items = db.query(TempStorageItem).filter(
            TempStorageItem.moved_to_storage_at.is_(None),
            TempStorageItem.created_at <= five_minutes_ago
        ).all()
        
        main_storage = await WarehouseService.get_main_storage_location(db)
        if not main_storage:
            logger.error("Основное хранилище не найдено")
            return
        
        temp_storage = await WarehouseService.get_temp_storage_location(db)
        if not temp_storage:
            logger.error("Временное хранилище не найдено")
            return
        
        for item in temp_items:
            # Проверяем место в основном хранилище
            has_space, available_space = await WarehouseService.check_capacity(db, main_storage.id, item.quantity_kg)
            
            if has_space:
                # Перемещаем в основное хранилище
                success = await inventory_client.create_operation(
                    operation_type="transfer",
                    sku_id=item.sku_id,
                    quantity_value=1,
                    quantity_unit="шт",
                    weight_value=item.quantity_kg,
                    weight_unit="кг",
                    source_location=temp_storage.name,
                    target_location=main_storage.name
                )
                
                if success:
                    await WarehouseService.update_location_capacity(db, temp_storage.id, -item.quantity_kg)
                    await WarehouseService.update_location_capacity(db, main_storage.id, item.quantity_kg)
                    item.moved_to_storage_at = datetime.now()
                    db.commit()
                    logger.info(f"Перемещен товар {item.sku_name} ({item.quantity_kg} кг) из временного хранилища в основное")
            else:
                # Оставляем во временном хранилище, будет обработано позже
                logger.warning(f"Недостаточно места в основном хранилище для товара {item.sku_name} ({item.quantity_kg} кг)")

