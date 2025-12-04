"""
Клиент для работы с Inventory Service
"""
import httpx
import logging
from typing import Optional, Dict, List
from app.config import settings

logger = logging.getLogger(__name__)


class InventoryClient:
    """Клиент для работы с Inventory Service"""
    
    def __init__(self):
        self.base_url = settings.INVENTORY_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_location_totals(self, location_name: Optional[str] = None) -> List[Dict]:
        """Получить остатки по локациям"""
        try:
            params = {}
            if location_name:
                params["location_name"] = location_name
            
            response = await self.client.get(
                f"{self.base_url}/inventory/locations",
                params=params
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error fetching location totals from Inventory Service: {e}")
            return []
    
    async def create_operation(
        self,
        operation_type: str,
        sku_id: int,
        quantity_value: int,
        quantity_unit: str,
        weight_value: int,
        weight_unit: str,
        source_location: Optional[str] = None,
        target_location: Optional[str] = None
    ) -> bool:
        """Создать операцию в Inventory Service"""
        try:
            response = await self.client.post(
                f"{self.base_url}/inventory/operations",
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
    
    async def close(self):
        """Закрыть клиент"""
        await self.client.aclose()


# Глобальный экземпляр клиента
inventory_client = InventoryClient()

