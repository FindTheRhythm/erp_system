"""
Клиент для получения данных из Catalog Service
"""
import httpx
import logging
from typing import Optional, Dict
from app.config import settings

logger = logging.getLogger(__name__)


class CatalogClient:
    """Клиент для работы с Catalog Service"""
    
    def __init__(self):
        self.base_url = settings.CATALOG_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_sku(self, sku_id: int) -> Optional[Dict]:
        """Получить информацию о товаре по ID"""
        try:
            response = await self.client.get(f"{self.base_url}/catalog/skus/{sku_id}")
            if response.status_code == 200:
                return response.json()
            logger.warning(f"SKU {sku_id} not found in Catalog Service")
            return None
        except Exception as e:
            logger.error(f"Error fetching SKU {sku_id} from Catalog Service: {e}")
            return None
    
    async def get_quantity_unit_coefficient(self, quantity_unit_name: str) -> int:
        """
        Получить коэффициент для единицы количества по её названию.
        Коэффициенты: шт=1, уп=25, ящ=125, пал=625
        """
        # Определяем коэффициент по названию единицы
        coefficients = {
            'шт': 1,
            'уп': 25,
            'ящ': 125,
            'пал': 625
        }
        return coefficients.get(quantity_unit_name.lower(), 1)
    
    async def get_quantity_unit_id_by_name(self, quantity_unit_name: str) -> Optional[int]:
        """
        Получить ID единицы количества по её названию из Catalog Service
        """
        try:
            response = await self.client.get(f"{self.base_url}/catalog/units?type=quantity")
            if response.status_code == 200:
                units = response.json()
                # Находим единицу по названию
                for unit in units:
                    if unit['name'].lower() == quantity_unit_name.lower():
                        return unit['id']
            return None
        except Exception as e:
            logger.error(f"Error fetching quantity unit ID: {e}")
            return None
    
    async def close(self):
        """Закрыть клиент"""
        await self.client.aclose()


# Глобальный экземпляр клиента
catalog_client = CatalogClient()

