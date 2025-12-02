from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "rabbitmq"
    RABBITMQ_PASSWORD: str = "rabbitmq_password"
    
    # Hardcoded users (admin/admin, viewer/viewer)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    VIEWER_USERNAME: str = "viewer"
    VIEWER_PASSWORD: str = "viewer"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

