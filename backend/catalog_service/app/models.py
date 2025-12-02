from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class SKUStatus(str, enum.Enum):
    """Статус товара"""
    AVAILABLE = "available"  # есть
    UNAVAILABLE = "unavailable"  # отсутствует
    UNKNOWN = "unknown"  # неизвестно


class UnitType(str, enum.Enum):
    """Тип единицы измерения"""
    weight = "weight"  # вес
    quantity = "quantity"  # количество
    price = "price"  # цена


class Unit(Base):
    """Единица измерения"""
    __tablename__ = "units"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=False, unique=True)  # кг, шт, руб и т.д.
    type = Column(SQLEnum(UnitType), nullable=False)  # вес, количество, цена
    description = Column(String(100), nullable=True)


class SKU(Base):
    """Товар (SKU - Stock Keeping Unit)"""
    __tablename__ = "skus"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(9), nullable=False, unique=True, index=True)  # XXXX-XXXX (8 символов + дефис)
    name = Column(String(15), nullable=False)
    weight = Column(String(5), nullable=False, default="1")  # значение
    weight_unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    quantity = Column(String(5), nullable=False, default="1")  # значение
    quantity_unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    description = Column(String(500), nullable=True)
    price = Column(String(5), nullable=True)  # значение
    price_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    status = Column(String(20), nullable=True, default="unknown")
    photo_url = Column(String(255), nullable=True)
    
    # Relationships
    weight_unit = relationship("Unit", foreign_keys=[weight_unit_id])
    quantity_unit = relationship("Unit", foreign_keys=[quantity_unit_id])
    price_unit = relationship("Unit", foreign_keys=[price_unit_id])

