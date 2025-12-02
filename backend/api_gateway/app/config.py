from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AUTH_SERVICE_URL: str = "http://auth_service:8000"
    CATALOG_SERVICE_URL: str = "http://catalog_service:8000"
    INVENTORY_SERVICE_URL: str = "http://inventory_service:8000"
    WAREHOUSE_SERVICE_URL: str = "http://warehouse_service:8000"
    ORDERS_SERVICE_URL: str = "http://orders_service:8000"
    NOTIFICATIONS_SERVICE_URL: str = "http://notifications_service:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

