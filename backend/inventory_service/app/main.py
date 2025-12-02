from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import inventory
from app.database import engine, Base
from app.config import settings
import logging
import os
from alembic.config import Config
from alembic import command

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Inventory Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(inventory.router)


# Инициализация Alembic
def run_migrations():
    logger.info("Running database migrations...")
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("script_location", "alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "postgresql://erp_user:erp_password@postgres:5432/erp_db"))
    # Используем отдельную таблицу версий для Inventory Service
    alembic_cfg.set_main_option("version_table", "inventory_alembic_version")
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed.")
    except Exception as e:
        logger.error(f"Error during database migrations: {e}")
        # Продолжаем работу даже если миграции не удались (для отладки)


@app.on_event("startup")
async def startup_event():
    run_migrations()
    # RabbitMQ consumer отключен - используем прямые HTTP вызовы из Catalog Service
    # Это проще и надежнее для MVP
    logger.info("Inventory Service started - using direct HTTP calls from Catalog Service")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Inventory Service shutting down")


@app.get("/")
async def root():
    return {"message": "Inventory Service", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
