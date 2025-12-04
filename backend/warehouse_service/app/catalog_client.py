"""
Клиент для получения данных из Catalog Service
"""
import httpx
import logging
from typing import Optional, Dict, List
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
    
    async def get_all_skus(self) -> List[Dict]:
        """Получить все товары"""
        try:
            response = await self.client.get(f"{self.base_url}/catalog/skus?limit=1000")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error fetching all SKUs from Catalog Service: {e}")
            return []
    
    async def close(self):
        """Закрыть клиент"""
        await self.client.aclose()


# Глобальный экземпляр клиента
catalog_client = CatalogClient()

