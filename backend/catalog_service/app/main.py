from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import catalog
from app.database import engine, Base
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создание таблиц (для разработки, в продакшене использовать миграции)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Catalog Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(catalog.router)


@app.get("/")
async def root():
    return {"message": "Catalog Service", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

