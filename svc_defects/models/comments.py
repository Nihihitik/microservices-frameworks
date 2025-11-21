from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .defects import Base


class Comment(Base):
    """SQLAlchemy-модель таблицы комментариев к дефекту"""

    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    defect = relationship("Defects", backref="comments")
