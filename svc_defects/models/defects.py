from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, UTC, date
from enum import Enum


class DefectPriority(str, Enum):
    """Приоритеты дефектов"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DefectStatus(str, Enum):
    """Статусы дефектов"""
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    ON_REVIEW = "ON_REVIEW"
    CLOSED = "CLOSED"
    CANCELED = "CANCELED"


class Defects(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Уникальный идентификатор дефекта")
    project_id: UUID = Field(..., description="ID проекта, к которому относится дефект")
    title: str = Field(..., description="Заголовок дефекта")
    description: str = Field(..., description="Подробное описание дефекта")
    priority: DefectPriority = Field(..., description="Приоритет дефекта")
    status: DefectStatus = Field(..., description="Статус дефекта")
    author_id: UUID = Field(..., description="ID пользователя, создавшего дефект")
    assignee_id: UUID | None = Field(None, description="ID назначенного исполнителя дефекта")
    due_date: date | None = Field(None, description="Срок устранения дефекта")
    location: str | None = Field(None, description="Зона/помещение на объекте, где обнаружен дефект")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Дата и время создания записи")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Дата и время последнего обновления записи")
