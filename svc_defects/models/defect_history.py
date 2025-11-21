from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, UTC


class DefectHistory(BaseModel):
    """Модель истории изменений дефекта"""
    id: UUID = Field(default_factory=uuid4, description="Уникальный идентификатор записи истории")
    defect_id: UUID = Field(..., description="ID дефекта, для которого зафиксировано изменение")
    changed_by_id: UUID = Field(..., description="ID пользователя, внесшего изменение")
    field_name: str = Field(..., description="Название измененного поля (например: status, assignee_id, priority)")
    old_value: str | None = Field(None, description="Старое значение поля")
    new_value: str | None = Field(None, description="Новое значение поля")
    changed_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Дата и время изменения")
