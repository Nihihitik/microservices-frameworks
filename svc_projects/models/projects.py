from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from enum import Enum


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


class Projects(BaseModel):
    id: UUID
    name: str = Field(..., description="Название объекта/проекта")
    code: str | None = Field(None, description="Внутренний код объекта")
    address: str = Field(..., description="Адрес объекта")
    customer_name: str = Field(..., description="Заказчик (организация/ФИО)")
    stage: ProjectStage = Field(..., description="Текущий этап проекта")
    status: ProjectStatus = Field(..., description="Общий статус проекта")
    manager_id: UUID = Field(..., description="ID менеджера, ведущего объект")
    start_date: date | None = Field(None, description="Дата начала проекта")
    end_date: date | None = Field(None, description="Дата окончания проекта")
    created_at: datetime = Field(..., description="Дата создания записи")
    updated_at: datetime = Field(..., description="Дата последнего обновления записи")
