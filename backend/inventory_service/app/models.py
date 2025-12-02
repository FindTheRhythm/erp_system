from sqlalchemy import Column, Integer, String, DateTime, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class OperationType(str):
    """Типы операций"""
    CREATE = "create"  # Создание товара
    UPDATE = "update"  # Изменение товара
    DELETE = "delete"  # Удаление товара
    RECEIPT = "receipt"  # Прием товара
    WRITE_OFF = "write_off"  # Списание товара
    TRANSFER = "transfer"  # Перемещение товара


class InventoryOperation(Base):
    """Операция с товаром"""
    __tablename__ = "inventory_operations"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(20), nullable=False, index=True)  # create/update/delete/receipt/write_off/transfer
    sku_id = Column(Integer, nullable=False, index=True)  # ID товара из Catalog Service
    sku_name = Column(String(15), nullable=False)  # Название товара
    quantity_value = Column(Integer, nullable=False)  # Значение количества (целое число)
    quantity_unit = Column(String(20), nullable=False)  # Единица количества (шт/уп/ящ/пал)
    weight_value = Column(Integer, nullable=False)  # Значение веса (целое число)
    weight_unit = Column(String(20), nullable=False)  # Единица веса (кг/г/т)
    delta_value = Column(Integer, nullable=False)  # Итоговое значение = количество*вес (например: +15 или -290)
    delta_unit = Column(String(20), nullable=False, default="кг")  # Единица итогового значения (обычно кг)
    source_location = Column(String(100), nullable=True)  # Начальная локация
    target_location = Column(String(100), nullable=True)  # Конечная локация (если одна локация, то = source_location)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InventorySKUTotal(Base):
    """Абсолютные остатки по SKU (сумма со всех локаций)"""
    __tablename__ = "inventory_sku_totals"
    
    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(Integer, nullable=False, unique=True, index=True)  # ID товара из Catalog Service
    sku_name = Column(String(15), nullable=False)  # Название товара
    total_quantity = Column(Integer, nullable=False, default=0)  # Общее количество
    total_weight = Column(Integer, nullable=False, default=0)  # Общий вес (в кг)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class InventoryLocationTotal(Base):
    """Остатки по локациям"""
    __tablename__ = "inventory_location_totals"
    
    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(Integer, nullable=False, index=True)  # ID товара из Catalog Service
    sku_name = Column(String(15), nullable=False)  # Название товара
    location_name = Column(String(100), nullable=False, index=True)  # Название локации из Warehouse Service
    quantity = Column(Integer, nullable=False, default=0)  # Количество в локации
    weight = Column(Integer, nullable=False, default=0)  # Вес в локации (в кг)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Уникальный индекс на комбинацию sku_id + location_name
    __table_args__ = (
        UniqueConstraint('sku_id', 'location_name', name='uq_inventory_location_sku_location'),
    )

