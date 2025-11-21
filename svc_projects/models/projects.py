from datetime import date, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base


class ProjectStage(str, Enum):
    """Этапы проекта"""

    DESIGN = "DESIGN"
    CONSTRUCTION = "CONSTRUCTION"
    FINISHING = "FINISHING"
    COMPLETED = "COMPLETED"


class ProjectStatus(str, Enum):
    """Статусы проекта"""

    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    CLOSED = "CLOSED"


Base = declarative_base()


class Projects(Base):
    """SQLAlchemy-модель таблицы проектов"""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    address = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=False)
    stage = Column(SAEnum(ProjectStage, name="project_stage"), nullable=False)
    status = Column(SAEnum(ProjectStatus, name="project_status"), nullable=False)
    manager_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
