"""
Клиент для вызова Inventory Service
"""
import httpx
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

INVENTORY_SERVICE_URL = "http://inventory_service:8000"


async def get_sku_total_weight(sku_id: int) -> Optional[int]:
    """
    Получить текущий total_weight для SKU из Inventory Service
    
    Returns:
        total_weight или None если не найдено
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{INVENTORY_SERVICE_URL}/inventory/sku/totals",
                params={"sku_id": sku_id}
            )
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0].get('total_weight', 0)
            return None
    except Exception as e:
        logger.error(f"Error getting SKU total weight: {e}")
        return None


async def create_inventory_operation(
    operation_type: str,
    sku_id: int,
    quantity_value: int,
    quantity_unit: str,
    weight_value: int,
    weight_unit: str,
    source_location: Optional[str] = None,
    target_location: Optional[str] = None
) -> bool:
    """
    Создать операцию в Inventory Service
    
    Returns:
        True если операция создана успешно, False в противном случае
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{INVENTORY_SERVICE_URL}/inventory/operations",
                json={
                    "operation_type": operation_type,
                    "sku_id": sku_id,
                    "quantity_value": quantity_value,
                    "quantity_unit": quantity_unit,
                    "weight_value": weight_value,
                    "weight_unit": weight_unit,
                    "source_location": source_location,
                    "target_location": target_location
                }
            )
            if response.status_code in [200, 201]:
                logger.info(f"Successfully created inventory operation: {operation_type} for SKU {sku_id}")
                return True
            else:
                logger.error(f"Failed to create inventory operation: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error calling Inventory Service: {e}")
        return False

