from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, UTC


class Attachment(BaseModel):
    """Модель вложения к дефекту"""
    id: UUID = Field(default_factory=uuid4, description="Уникальный идентификатор вложения")
    defect_id: UUID = Field(..., description="ID дефекта, к которому относится вложение")
    file_url: str = Field(..., description="Путь до файла (S3/локальное хранилище и т.п.)")
    file_name: str = Field(..., description="Имя файла")
    uploaded_by_id: UUID = Field(..., description="ID пользователя, загрузившего файл")
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Дата и время загрузки файла")
