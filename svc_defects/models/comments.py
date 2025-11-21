from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, UTC


class Comment(BaseModel):
    """Модель комментария к дефекту"""
    id: UUID = Field(default_factory=uuid4, description="Уникальный идентификатор комментария")
    defect_id: UUID = Field(..., description="ID дефекта, к которому относится комментарий")
    author_id: UUID = Field(..., description="ID пользователя, оставившего комментарий")
    text: str = Field(..., description="Текст комментария")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Дата и время создания комментария")
