from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from contextlib import asynccontextmanager

from app.routers import warehouse
from app.warehouse_service import WarehouseService
from app.database import SessionLocal

logger = logging.getLogger(__name__)


async def process_temp_storage_periodically():
    """Периодическая обработка временного хранилища"""
    while True:
        try:
            await asyncio.sleep(60)  # Проверяем каждую минуту
            db = SessionLocal()
            try:
                await WarehouseService.process_temp_storage_migration(db)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Ошибка при обработке временного хранилища: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Warehouse Service...")
    # Инициализация данных
    from app.init_data import init_locations
    init_locations()
    
    # Запускаем фоновую задачу для обработки временного хранилища
    task = asyncio.create_task(process_temp_storage_periodically())
    
    yield
    
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Shutting down Warehouse Service...")


app = FastAPI(
    title="Warehouse Service",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(warehouse.router)

@app.get("/")
async def root():
    return {"message": "Warehouse Service", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

