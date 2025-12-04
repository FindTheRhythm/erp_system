from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import LocationType, OperationType


class LocationBase(BaseModel):
    name: str = Field(..., max_length=100, description="Название локации")
    type: LocationType = Field(..., description="Тип локации")
    max_capacity_kg: int = Field(..., ge=0, description="Максимальная вместимость в кг")
    description: Optional[str] = Field(None, max_length=500, description="Описание")


class LocationCreate(LocationBase):
    pass


class LocationResponse(LocationBase):
    id: int
    current_capacity_kg: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LocationStatsResponse(BaseModel):
    """Статистика по локации"""
    id: int
    name: str
    type: LocationType
    max_capacity_kg: int
    current_capacity_kg: int
    usage_percent: float  # Процент заполнения
    description: Optional[str]
    
    class Config:
        from_attributes = True


class WarehouseOperationBase(BaseModel):
    operation_type: OperationType = Field(..., description="Тип операции")
    sku_id: Optional[int] = Field(None, description="ID товара (null для операций со всеми товарами)")
    source_location_id: Optional[int] = Field(None, description="Исходная локация")
    target_location_id: Optional[int] = Field(None, description="Целевая локация")


class WarehouseOperationCreate(WarehouseOperationBase):
    pass


class WarehouseOperationResponse(WarehouseOperationBase):
    id: int
    sku_name: Optional[str]
    quantity_kg: int
    status: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TempStorageItemResponse(BaseModel):
    """Элемент временного хранилища"""
    id: int
    sku_id: int
    sku_name: str
    quantity_kg: int
    source_operation_id: Optional[int]
    created_at: datetime
    moved_to_storage_at: Optional[datetime]
    
    class Config:
        from_attributes = True

