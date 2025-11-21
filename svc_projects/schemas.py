from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from .models.projects import ProjectStage, ProjectStatus

try:  # Pydantic v2
    from pydantic import ConfigDict
except ImportError:  # Pydantic v1 – модель просто проигнорирует model_config
    ConfigDict = dict  # type: ignore[misc,assignment]


class ProjectBase(BaseModel):
    """Базовая схема проекта для API."""

    name: str
    code: Optional[str] = None
    address: str
    customer_name: str
    stage: ProjectStage
    status: ProjectStatus
    manager_id: UUID
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    """Схема создания проекта."""

    pass


class ProjectUpdate(BaseModel):
    """Схема частичного обновления проекта."""

    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    customer_name: Optional[str] = None
    stage: Optional[ProjectStage] = None
    status: Optional[ProjectStatus] = None
    manager_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectRead(ProjectBase):
    """Схема чтения проекта (ответ API)."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
