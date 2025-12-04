from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://erp_user:erp_password@postgres:5432/erp_db"
    
    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "rabbitmq"
    RABBITMQ_PASSWORD: str = "rabbitmq_password"
    
    # External Services URLs
    CATALOG_SERVICE_URL: str = "http://catalog_service:8000"
    INVENTORY_SERVICE_URL: str = "http://inventory_service:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

