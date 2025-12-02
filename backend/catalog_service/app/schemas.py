from pydantic import BaseModel, Field, validator
from typing import Optional
from app.models import SKUStatus


class UnitBase(BaseModel):
    name: str = Field(..., max_length=20, description="Название единицы измерения")
    type: str = Field(..., description="Тип: weight, quantity, price")
    description: Optional[str] = Field(None, max_length=100, description="Описание")


class UnitCreate(UnitBase):
    pass


class UnitResponse(UnitBase):
    id: int
    
    class Config:
        from_attributes = True


class SKUBase(BaseModel):
    code: str = Field(..., max_length=9, description="Артикул в формате XXXX-XXXX")
    name: str = Field(..., max_length=15, description="Название товара")
    weight: str = Field(..., max_length=5, description="Вес")
    weight_unit_id: int = Field(..., description="ID единицы измерения веса")
    quantity: str = Field(..., max_length=5, description="Количество")
    quantity_unit_id: int = Field(..., description="ID единицы измерения количества")
    description: Optional[str] = Field(None, max_length=120, description="Описание")
    price: Optional[str] = Field(None, max_length=5, description="Цена")
    price_unit_id: Optional[int] = Field(None, description="ID единицы измерения цены")
    status: Optional[SKUStatus] = Field(SKUStatus.UNKNOWN, description="Статус товара")
    photo_url: Optional[str] = Field(None, max_length=255, description="Ссылка на фото")
    
    @validator('code')
    def validate_code(cls, v):
        """Валидация формата артикула: XXXX-XXXX (латиница/цифры, большие буквы)"""
        if not v:
            raise ValueError('Артикул не может быть пустым')
        
        # Проверка формата XXXX-XXXX
        parts = v.split('-')
        if len(parts) != 2:
            raise ValueError('Артикул должен быть в формате XXXX-XXXX')
        
        if len(parts[0]) != 4 or len(parts[1]) != 4:
            raise ValueError('Каждая часть артикула должна содержать 4 символа')
        
        # Проверка что только латиница (большие буквы) и цифры
        import re
        pattern = r'^[A-Z0-9]+$'
        if not re.match(pattern, parts[0]) or not re.match(pattern, parts[1]):
            raise ValueError('Артикул должен содержать только латинские буквы (большие) и цифры')
        
        return v.upper()  # Приводим к верхнему регистру
    
    @validator('status', pre=True)
    def validate_status(cls, v):
        """Валидация статуса: преобразуем строку в enum"""
        if v is None:
            return SKUStatus.UNKNOWN
        if isinstance(v, str):
            # Преобразуем строку в enum (нижний регистр)
            try:
                return SKUStatus(v.lower())
            except ValueError:
                return SKUStatus.UNKNOWN
        if isinstance(v, SKUStatus):
            return v
        return SKUStatus.UNKNOWN


class SKUCreate(SKUBase):
    pass


class SKUUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=15)
    weight: Optional[str] = Field(None, max_length=5)
    weight_unit_id: Optional[int] = None
    quantity: Optional[str] = Field(None, max_length=5)
    quantity_unit_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=120)
    price: Optional[str] = Field(None, max_length=5)
    price_unit_id: Optional[int] = None
    status: Optional[SKUStatus] = None
    photo_url: Optional[str] = Field(None, max_length=255)


class SKUResponse(SKUBase):
    id: int
    weight_unit: Optional[UnitResponse] = None
    quantity_unit: Optional[UnitResponse] = None
    price_unit: Optional[UnitResponse] = None
    
    class Config:
        from_attributes = True


class SKUListResponse(BaseModel):
    """Ответ для списка товаров (без деталей единиц измерения)"""
    id: int
    code: str
    name: str
    weight: str
    quantity: str
    status: Optional[SKUStatus]
    
    class Config:
        from_attributes = True

