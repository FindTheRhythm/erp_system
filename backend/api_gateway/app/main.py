from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.proxy import router as proxy_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "API Gateway", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

# Подключение прокси роутера (после основных роутеров, чтобы не перехватывать их)
app.include_router(proxy_router)

