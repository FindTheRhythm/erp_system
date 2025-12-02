from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://erp_user:erp_password@postgres:5432/erp_db"
    
    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "rabbitmq"
    RABBITMQ_PASSWORD: str = "rabbitmq_password"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


