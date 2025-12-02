from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OperationCreate(BaseModel):
    """Схема для создания операции"""
    operation_type: str = Field(..., description="Тип операции: create/update/delete/receipt/write_off/transfer")
    sku_id: int = Field(..., description="ID товара из Catalog Service")
    quantity_value: int = Field(..., description="Значение количества (целое число)")
    quantity_unit: str = Field(..., description="Единица количества (шт/уп/ящ/пал)")
    weight_value: int = Field(..., description="Значение веса (целое число)")
    weight_unit: str = Field(..., description="Единица веса (кг/г/т)")
    source_location: Optional[str] = Field(None, description="Начальная локация")
    target_location: Optional[str] = Field(None, description="Конечная локация")


class OperationResponse(BaseModel):
    """Схема ответа для операции"""
    id: int
    operation_type: str
    sku_id: int
    sku_name: str
    quantity_value: int
    quantity_unit: str
    weight_value: int
    weight_unit: str
    delta_value: int
    delta_unit: str
    source_location: Optional[str]
    target_location: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SKUTotalResponse(BaseModel):
    """Схема ответа для абсолютных остатков по SKU"""
    id: int
    sku_id: int
    sku_name: str
    total_quantity: int
    total_weight: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LocationTotalResponse(BaseModel):
    """Схема ответа для остатков по локации"""
    id: int
    sku_id: int
    sku_name: str
    location_name: str
    quantity: int
    weight: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


