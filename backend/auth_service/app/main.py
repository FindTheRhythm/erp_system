from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Auth Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Auth Service", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

