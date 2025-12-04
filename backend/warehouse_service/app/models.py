from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class LocationType(str, enum.Enum):
    """Тип локации"""
    STORAGE = "storage"  # Хранилище
    WAREHOUSE = "warehouse"  # Склад
    TEMP_STORAGE = "temp_storage"  # Временное хранилище


class OperationType(str, enum.Enum):
    """Тип операции перемещения"""
    # Локальные операции (1-2 локации)
    RECEIPT = "receipt"  # Прием товара складом из хранилища
    SHIPMENT = "shipment"  # Отгрузка товара со склада в хранилище
    TRANSFER = "transfer"  # Перемещение между складами
    
    # Глобальные операции
    GLOBAL_DISTRIBUTION_ALL = "global_distribution_all"  # Глобальное распределение (все товары)
    GLOBAL_DISTRIBUTION_SKU = "global_distribution_sku"  # Глобальное распределение (товар)
    REPLENISHMENT_ALL = "replenishment_all"  # Пополнение запасов (все товары)
    REPLENISHMENT_SKU = "replenishment_sku"  # Пополнение запасов (товар)
    PLACEMENT_ALL = "placement_all"  # Размещение запасов (все товары)
    PLACEMENT_SKU = "placement_sku"  # Размещение запасов (товар)


class Location(Base):
    """Склад/хранилище"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)  # Название локации
    type = Column(SQLEnum(LocationType), nullable=False)  # Тип локации
    max_capacity_kg = Column(Integer, nullable=False)  # Максимальная вместимость в кг
    current_capacity_kg = Column(Integer, nullable=False, default=0)  # Текущая заполненность в кг
    description = Column(String(500), nullable=True)  # Описание
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    source_operations = relationship("WarehouseOperation", foreign_keys="WarehouseOperation.source_location_id", back_populates="source_location")
    target_operations = relationship("WarehouseOperation", foreign_keys="WarehouseOperation.target_location_id", back_populates="target_location")


class WarehouseOperation(Base):
    """Операция перемещения товаров"""
    __tablename__ = "warehouse_operations"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(SQLEnum(OperationType), nullable=False)  # Тип операции
    sku_id = Column(Integer, nullable=True, index=True)  # ID товара (null для операций со всеми товарами)
    sku_name = Column(String(15), nullable=True)  # Название товара
    source_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Исходная локация
    target_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Целевая локация
    quantity_kg = Column(Integer, nullable=False)  # Количество в кг
    status = Column(String(20), nullable=False, default="pending")  # Статус: pending, completed, failed
    error_message = Column(String(500), nullable=True)  # Сообщение об ошибке
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    source_location = relationship("Location", foreign_keys=[source_location_id], back_populates="source_operations")
    target_location = relationship("Location", foreign_keys=[target_location_id], back_populates="target_operations")


class TempStorageItem(Base):
    """Временное хранилище для излишков товаров"""
    __tablename__ = "temp_storage_items"
    
    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(Integer, nullable=False, index=True)  # ID товара
    sku_name = Column(String(15), nullable=False)  # Название товара
    quantity_kg = Column(Integer, nullable=False)  # Количество в кг
    source_operation_id = Column(Integer, ForeignKey("warehouse_operations.id"), nullable=True)  # Операция, которая создала этот излишек
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    moved_to_storage_at = Column(DateTime(timezone=True), nullable=True)  # Когда перемещен в хранилище

