from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base


class Role(str, Enum):
    """Роли пользователей в системе"""

    ENGINEER = "engineer"  # Инженер
    ADMIN = "admin"  # Администратор
    SUPERVISOR = "supervisor"  # Руководитель
    CUSTOMER = "customer"  # Заказчик


Base = declarative_base()


class Users(Base):
    """SQLAlchemy-модель таблицы пользователей"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    full_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hash_password = Column(String(128), nullable=False)
    role = Column(SAEnum(Role, name="role"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
