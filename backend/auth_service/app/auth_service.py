from app.config import settings
from app.models import LoginRequest, LoginResponse, LogoutResponse
from app.rabbitmq_client import rabbitmq_client
from typing import Literal, Optional
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис авторизации с хардкод пользователями"""
    
    @staticmethod
    def validate_user(username: str, password: str) -> Optional[Literal["admin", "viewer"]]:
        """Проверить логин и пароль, вернуть роль если валидно"""
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            return "admin"
        elif username == settings.VIEWER_USERNAME and password == settings.VIEWER_PASSWORD:
            return "viewer"
        return None
    
    @staticmethod
    def login(username: str, password: str) -> LoginResponse:
        """Выполнить вход пользователя"""
        role = AuthService.validate_user(username, password)
        
        if role:
            # Отправить событие в RabbitMQ
            rabbitmq_client.publish_event("login", {
                "username": username,
                "role": role
            })
            
            logger.info(f"User {username} ({role}) logged in")
            
            return LoginResponse(
                success=True,
                message="Успешный вход",
                role=role
            )
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return LoginResponse(
                success=False,
                message="Неверный логин или пароль",
                role=None
            )
    
    @staticmethod
    def logout(username: str, role: str) -> LogoutResponse:
        """Выполнить выход пользователя"""
        # Отправить событие в RabbitMQ
        rabbitmq_client.publish_event("logout", {
            "username": username,
            "role": role
        })
        
        logger.info(f"User {username} ({role}) logged out")
        
        return LogoutResponse(
            success=True,
            message="Успешный выход"
        )

