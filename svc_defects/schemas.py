from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from .models.defects import DefectPriority, DefectStatus

try:  # Pydantic v2
    from pydantic import ConfigDict
except ImportError:  # Pydantic v1 – модель просто проигнорирует model_config
    ConfigDict = dict  # type: ignore[misc,assignment]


# --------- Дефекты ---------


class DefectBase(BaseModel):
    """Базовая схема дефекта для API."""

    project_id: UUID
    title: str
    description: str
    priority: DefectPriority
    assignee_id: Optional[UUID] = None
    due_date: Optional[date] = None
    location: Optional[str] = None


class DefectCreate(DefectBase):
    """Схема создания дефекта.

    author_id обычно берётся из текущего пользователя, но оставлен явным полем,
    чтобы сохранить гибкость.
    """

    status: DefectStatus = DefectStatus.NEW
    author_id: UUID


class DefectUpdate(BaseModel):
    """Схема частичного обновления дефекта."""

    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[DefectPriority] = None
    status: Optional[DefectStatus] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[date] = None
    location: Optional[str] = None


class DefectRead(DefectBase):
    """Схема чтения дефекта (ответ API)."""

    id: UUID
    status: DefectStatus
    author_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------- Комментарии ---------


class CommentBase(BaseModel):
    """Базовая схема комментария."""

    text: str


class CommentCreate(CommentBase):
    """Схема создания комментария."""

    defect_id: UUID
    author_id: UUID


class CommentRead(CommentBase):
    """Схема чтения комментария."""

    id: UUID
    defect_id: UUID
    author_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------- Вложения ---------


class AttachmentBase(BaseModel):
    """Базовая схема вложения."""

    file_url: str
    file_name: str


class AttachmentCreate(AttachmentBase):
    """Схема создания вложения."""

    defect_id: UUID
    uploaded_by_id: UUID


class AttachmentRead(AttachmentBase):
    """Схема чтения вложения."""

    id: UUID
    defect_id: UUID
    uploaded_by_id: UUID
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------- История дефекта ---------


class DefectHistoryEntryBase(BaseModel):
    """Базовая схема записи истории изменения дефекта."""

    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class DefectHistoryEntryCreate(DefectHistoryEntryBase):
    """Схема создания записи истории."""

    defect_id: UUID
    changed_by_id: UUID


class DefectHistoryEntryRead(DefectHistoryEntryBase):
    """Схема чтения записи истории."""

    id: UUID
    defect_id: UUID
    changed_by_id: UUID
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)
