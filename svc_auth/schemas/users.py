from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from models.users import Role

try:  # Pydantic v2
    from pydantic import ConfigDict
except ImportError:  # Pydantic v1 – модель просто проигнорирует model_config
    ConfigDict = dict  # type: ignore[misc,assignment]


class UserBase(BaseModel):
    """Базовая схема пользователя для API."""

    full_name: str
    email: EmailStr
    role: Role
    is_active: bool = True


class UserCreate(UserBase):
    """Схема создания пользователя (регистрация/админское создание)."""

    password: str


class UserUpdate(BaseModel):
    """Схема частичного обновления пользователя."""

    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserRead(UserBase):
    """Схема чтения пользователя (ответ API)."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    # Поддержка from_attributes в Pydantic v2 (и безопасно для v1)
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT-токен, возвращаемый при логине."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Полезная нагрузка JWT (из ABOUT.md)."""

    sub: UUID
    role: Role
    exp: int
