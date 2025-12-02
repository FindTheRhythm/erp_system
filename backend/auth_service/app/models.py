from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
import re


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=5, description="Логин (минимум 5 символов, только латиница)")
    password: str = Field(..., min_length=5, description="Пароль (минимум 5 символов, только латиница)")
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Логин должен содержать только латинские буквы, цифры и подчеркивание')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Пароль должен содержать только латинские буквы, цифры и подчеркивание')
        return v


class LoginResponse(BaseModel):
    success: bool
    message: str
    role: Optional[Literal["admin", "viewer"]] = None


class LogoutRequest(BaseModel):
    username: str
    role: str


class LogoutResponse(BaseModel):
    success: bool
    message: str
