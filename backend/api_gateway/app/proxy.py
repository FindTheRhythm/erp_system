from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


async def proxy_request(
    request: Request,
    service_url: str,
    path: str
) -> Response:
    """Проксировать запрос к микросервису"""
    url = f"{service_url}{path}"
    
    logger.info(f"Proxying {request.method} {request.url.path} to {url}")
    
    # Получить тело запроса
    body = await request.body()
    
    # Получить заголовки (исключая host и connection)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("connection", None)
    
    # Передаем роль пользователя из сессии (для MVP используем заголовок)
    # В реальном приложении это должно быть из JWT токена
    # Пока используем заголовок X-User-Role, который должен передавать frontend
    # Если заголовок не передан, используем viewer по умолчанию
    if "x-user-role" not in headers:
        headers["X-User-Role"] = "viewer"  # По умолчанию viewer
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers=headers,
                params=request.query_params,
                timeout=30.0
            )
            
            logger.info(f"Response from {url}: {response.status_code}")
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        except httpx.RequestError as e:
            logger.error(f"Request error to {url}: {str(e)}")
            return Response(
                content=f'{{"error": "Service unavailable: {str(e)}"}}',
                status_code=503,
                media_type="application/json"
            )


@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def auth_proxy(request: Request, path: str):
    """Проксировать запросы к Auth Service"""
    logger.info(f"Auth proxy called: path={path}, method={request.method}")
    # Если path пустой, используем полный путь /auth
    full_path = f"/auth/{path}" if path else "/auth"
    return await proxy_request(request, settings.AUTH_SERVICE_URL, full_path)


@router.api_route("/catalog/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catalog_proxy(request: Request, path: str):
    """Проксировать запросы к Catalog Service"""
    logger.info(f"Catalog proxy called: path={path}, method={request.method}, full_url={request.url.path}")
    # Если path пустой, используем полный путь /catalog
    full_path = f"/catalog/{path}" if path else "/catalog"
    logger.info(f"Proxying to: {settings.CATALOG_SERVICE_URL}{full_path}")
    return await proxy_request(request, settings.CATALOG_SERVICE_URL, full_path)


@router.api_route("/inventory/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def inventory_proxy(request: Request, path: str):
    """Проксировать запросы к Inventory Service"""
    logger.info(f"Inventory proxy called: path={path}, method={request.method}, full_url={request.url.path}")
    # Inventory Service роутер имеет префикс /inventory, поэтому добавляем его к пути
    # Если path пустой, используем "/inventory/"
    if path:
        full_path = f"/inventory/{path}"
    else:
        full_path = "/inventory/"
    logger.info(f"Proxying to: {settings.INVENTORY_SERVICE_URL}{full_path}")
    return await proxy_request(request, settings.INVENTORY_SERVICE_URL, full_path)

