from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, LargeBinary, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .defects import Base


class Attachment(Base):
    """SQLAlchemy-модель таблицы вложений к дефекту

    Хранит файлы (фото) напрямую в БД в виде бинарных данных.
    """

    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_data = Column(LargeBinary, nullable=False)  # Бинарные данные файла
    file_size = Column(Integer, nullable=False)  # Размер файла в байтах
    content_type = Column(String(100), nullable=False)  # MIME тип (image/jpeg, image/png, etc.)
    uploaded_by_id = Column(UUID(as_uuid=True), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    defect = relationship("Defects", backref="attachments")
