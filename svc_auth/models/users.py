from pydantic import BaseModel, Field, EmailStr
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum


class Role(str, Enum):
    """Роли пользователей в системе"""
    ENGINEER = "engineer"  # Инженер
    ADMIN = "admin"  # Администратор
    SUPERVISOR = "supervisor"  # Руководитель
    CUSTOMER = "customer"  # Заказчик


class Users(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Уникальный идентификатор пользователя")
    full_name: str = Field(..., min_length=3, max_length=50, description="Полное имя пользователя")
    email: EmailStr = Field(..., description="Email адрес пользователя")
    hash_password: str = Field(..., min_length=3, max_length=32, description="Хешированный пароль пользователя")
    role: Role = Field(..., description="Роль пользователя в системе")
    is_active: bool = Field(default=True, description="Флаг активности пользователя")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Дата и время создания записи")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Дата и время последнего обновления записи")
