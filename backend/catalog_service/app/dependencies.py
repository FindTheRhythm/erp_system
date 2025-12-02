from fastapi import Header, HTTPException
from typing import Optional


def get_user_role(x_user_role: Optional[str] = Header(None, alias="X-User-Role")) -> str:
    """
    Получить роль пользователя из заголовка запроса.
    В реальном приложении это должно быть из JWT токена или сессии.
    Для MVP используем заголовок X-User-Role, который будет передавать API Gateway.
    """
    if not x_user_role:
        raise HTTPException(status_code=401, detail="Роль пользователя не указана")
    
    if x_user_role not in ["admin", "viewer"]:
        raise HTTPException(status_code=403, detail="Неверная роль пользователя")
    
    return x_user_role


def require_admin_role(user_role: str = None):
    """Проверка что пользователь имеет роль admin"""
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен. Требуется роль администратора")


