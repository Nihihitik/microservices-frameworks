from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

try:  # Pydantic v2
    from pydantic import ConfigDict
except ImportError:
    ConfigDict = dict  # type: ignore


# --------- Enums (mirror from svc_defects) ---------


class DefectStatus(str, Enum):
    """Defect statuses"""

    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    ON_REVIEW = "ON_REVIEW"
    CLOSED = "CLOSED"
    CANCELED = "CANCELED"


class DefectPriority(str, Enum):
    """Defect priorities"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExportFormat(str, Enum):
    """Export file formats"""

    CSV = "csv"
    EXCEL = "xlsx"


# --------- Response Schemas ---------


class StatusDistribution(BaseModel):
    """Distribution of defects by status"""

    status: DefectStatus
    count: int


class PriorityDistribution(BaseModel):
    """Distribution of defects by priority"""

    priority: DefectPriority
    count: int


class ProjectSummary(BaseModel):
    """Summary statistics for a project"""

    project_id: UUID
    project_name: str
    total_defects: int
    status_distribution: List[StatusDistribution]
    priority_distribution: List[PriorityDistribution]
    average_resolution_time_days: Optional[float] = Field(
        None, description="Average time to close defects (in days)"
    )


class DefectSummaryReport(BaseModel):
    """
    Main summary report response.
    Can be aggregated by project or globally.
    """

    total_defects: int
    status_distribution: List[StatusDistribution]
    priority_distribution: List[PriorityDistribution]
    average_resolution_time_days: Optional[float] = None
    closed_defects_count: int
    open_defects_count: int

    # If filtered by project
    project_summary: Optional[ProjectSummary] = None

    # Metadata
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DefectListItem(BaseModel):
    """
    Simplified defect item for tabular reports.
    This is a flattened version of DefectRead from svc_defects.
    """

    id: UUID
    project_id: UUID
    project_name: Optional[str] = None  # Enriched from svc_projects
    title: str
    priority: DefectPriority
    status: DefectStatus
    author_id: UUID
    assignee_id: Optional[UUID] = None
    due_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    resolution_time_days: Optional[float] = None  # Calculated field


class DefectDetailedReport(BaseModel):
    """
    Detailed tabular report with all defects matching filters.
    Used for export and detailed analytics.
    """

    defects: List[DefectListItem]
    total_count: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
