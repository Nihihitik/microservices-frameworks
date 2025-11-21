from datetime import date, datetime, UTC
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, Enum as SAEnum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base


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


Base = declarative_base()


class Defects(Base):
    """SQLAlchemy-модель таблицы дефектов"""

    __tablename__ = "defects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(SAEnum(DefectPriority, name="defect_priority"), nullable=False)
    status = Column(SAEnum(DefectStatus, name="defect_status"), nullable=False)
    author_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    assignee_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    due_date = Column(Date, nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
