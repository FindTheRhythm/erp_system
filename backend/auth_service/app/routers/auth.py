from fastapi import APIRouter, HTTPException
from app.models import LoginRequest, LoginResponse, LogoutRequest, LogoutResponse
from app.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Вход пользователя"""
    response = AuthService.login(request.username, request.password)
    
    if not response.success:
        raise HTTPException(status_code=401, detail=response.message)
    
    return response


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: LogoutRequest):
    """Выход пользователя"""
    response = AuthService.logout(request.username, request.role)
    return response

