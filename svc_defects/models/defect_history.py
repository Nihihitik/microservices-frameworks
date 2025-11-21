from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .defects import Base


class DefectHistory(Base):
    """SQLAlchemy-модель таблицы истории изменений дефекта"""

    __tablename__ = "defect_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by_id = Column(UUID(as_uuid=True), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    defect = relationship("Defects", backref="history_entries")
