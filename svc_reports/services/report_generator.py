from collections import defaultdict
from datetime import date, datetime
from io import BytesIO
from typing import Dict, List, Optional
from uuid import UUID

import pandas as pd

from schemas.reports import (
    DefectDetailedReport,
    DefectListItem,
    DefectPriority,
    DefectStatus,
    DefectSummaryReport,
    PriorityDistribution,
    ProjectSummary,
    StatusDistribution,
)


class ReportGenerator:
    """
    Business logic for generating reports and statistics.
    """

    @staticmethod
    def filter_by_date_range(
        defects: List[Dict], start_date: Optional[date], end_date: Optional[date]
    ) -> List[Dict]:
        """
        Filter defects by creation date range.

        Args:
            defects: List of defect dictionaries
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Filtered list of defects
        """
        if not start_date and not end_date:
            return defects

        filtered = []
        for defect in defects:
            # Parse created_at (ISO format string to datetime)
            created_at_str = defect.get("created_at")
            if not created_at_str:
                continue

            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            created_date = created_at.date()

            if start_date and created_date < start_date:
                continue
            if end_date and created_date > end_date:
                continue

            filtered.append(defect)

        return filtered

    @staticmethod
    def calculate_status_distribution(defects: List[Dict]) -> List[StatusDistribution]:
        """
        Calculate count of defects by status.

        Returns:
            List of StatusDistribution objects
        """
        counts = defaultdict(int)
        for defect in defects:
            status = defect.get("status")
            if status:
                counts[status] += 1

        return [
            StatusDistribution(status=DefectStatus(s), count=c) for s, c in counts.items()
        ]

    @staticmethod
    def calculate_priority_distribution(
        defects: List[Dict],
    ) -> List[PriorityDistribution]:
        """
        Calculate count of defects by priority.

        Returns:
            List of PriorityDistribution objects
        """
        counts = defaultdict(int)
        for defect in defects:
            priority = defect.get("priority")
            if priority:
                counts[priority] += 1

        return [
            PriorityDistribution(priority=DefectPriority(p), count=c)
            for p, c in counts.items()
        ]

    @staticmethod
    def calculate_average_resolution_time(defects: List[Dict]) -> Optional[float]:
        """
        Calculate average time (in days) to close defects.

        Only considers defects with status=CLOSED.
        Uses updated_at as proxy for closed_at.

        Returns:
            Average resolution time in days, or None if no closed defects
        """
        resolution_times = []

        for defect in defects:
            if defect.get("status") != "CLOSED":
                continue

            created_at_str = defect.get("created_at")
            updated_at_str = defect.get("updated_at")  # Proxy for closed_at

            if not created_at_str or not updated_at_str:
                continue

            try:
                created_at = datetime.fromisoformat(
                    created_at_str.replace("Z", "+00:00")
                )
                updated_at = datetime.fromisoformat(
                    updated_at_str.replace("Z", "+00:00")
                )

                resolution_time = (
                    updated_at - created_at
                ).total_seconds() / 86400  # days
                resolution_times.append(resolution_time)
            except ValueError:
                continue

        if not resolution_times:
            return None

        return sum(resolution_times) / len(resolution_times)

    @staticmethod
    def generate_summary_report(
        defects: List[Dict],
        project: Optional[Dict] = None,
        filters: Optional[Dict] = None,
    ) -> DefectSummaryReport:
        """
        Generate summary statistics report.

        Args:
            defects: List of defect dictionaries
            project: Optional project dictionary (if filtered by single project)
            filters: Optional filters applied

        Returns:
            DefectSummaryReport object
        """
        total_defects = len(defects)

        status_dist = ReportGenerator.calculate_status_distribution(defects)
        priority_dist = ReportGenerator.calculate_priority_distribution(defects)
        avg_resolution = ReportGenerator.calculate_average_resolution_time(defects)

        closed_count = sum(1 for d in defects if d.get("status") == "CLOSED")
        open_count = sum(
            1 for d in defects if d.get("status") in ["NEW", "IN_PROGRESS", "ON_REVIEW"]
        )

        project_summary = None
        if project:
            project_summary = ProjectSummary(
                project_id=UUID(project["id"]),
                project_name=project.get("name", "Unknown"),
                total_defects=total_defects,
                status_distribution=status_dist,
                priority_distribution=priority_dist,
                average_resolution_time_days=avg_resolution,
            )

        return DefectSummaryReport(
            total_defects=total_defects,
            status_distribution=status_dist,
            priority_distribution=priority_dist,
            average_resolution_time_days=avg_resolution,
            closed_defects_count=closed_count,
            open_defects_count=open_count,
            project_summary=project_summary,
            filters_applied=filters or {},
            generated_at=datetime.utcnow(),
        )

    @staticmethod
    def generate_detailed_report(
        defects: List[Dict],
        projects_map: Optional[Dict[UUID, Dict]] = None,
        filters: Optional[Dict] = None,
    ) -> DefectDetailedReport:
        """
        Generate detailed tabular report with all defects.

        Args:
            defects: List of defect dictionaries
            projects_map: Optional mapping of project_id -> project dict (for enrichment)
            filters: Optional filters applied

        Returns:
            DefectDetailedReport object
        """
        defect_items = []

        for defect in defects:
            # Calculate resolution time for closed defects
            resolution_time = None
            if defect.get("status") == "CLOSED":
                created_at_str = defect.get("created_at")
                updated_at_str = defect.get("updated_at")

                if created_at_str and updated_at_str:
                    try:
                        created_at = datetime.fromisoformat(
                            created_at_str.replace("Z", "+00:00")
                        )
                        updated_at = datetime.fromisoformat(
                            updated_at_str.replace("Z", "+00:00")
                        )
                        resolution_time = (
                            updated_at - created_at
                        ).total_seconds() / 86400
                    except ValueError:
                        pass

            # Enrich with project name
            project_name = None
            project_id = UUID(defect["project_id"])
            if projects_map and project_id in projects_map:
                project_name = projects_map[project_id].get("name")

            defect_item = DefectListItem(
                id=UUID(defect["id"]),
                project_id=project_id,
                project_name=project_name,
                title=defect["title"],
                priority=DefectPriority(defect["priority"]),
                status=DefectStatus(defect["status"]),
                author_id=UUID(defect["author_id"]),
                assignee_id=UUID(defect["assignee_id"])
                if defect.get("assignee_id")
                else None,
                due_date=date.fromisoformat(defect["due_date"])
                if defect.get("due_date")
                else None,
                created_at=datetime.fromisoformat(
                    defect["created_at"].replace("Z", "+00:00")
                ),
                updated_at=datetime.fromisoformat(
                    defect["updated_at"].replace("Z", "+00:00")
                ),
                resolution_time_days=resolution_time,
            )

            defect_items.append(defect_item)

        return DefectDetailedReport(
            defects=defect_items,
            total_count=len(defect_items),
            filters_applied=filters or {},
            generated_at=datetime.utcnow(),
        )

    @staticmethod
    def export_to_csv(report: DefectDetailedReport) -> bytes:
        """
        Export detailed report to CSV format.

        Returns:
            CSV file as bytes
        """
        # Convert to DataFrame
        data = [defect.model_dump() for defect in report.defects]
        df = pd.DataFrame(data)

        # Convert UUID columns to strings
        uuid_columns = ["id", "project_id", "author_id", "assignee_id"]
        for col in uuid_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # Export to CSV
        buffer = BytesIO()
        df.to_csv(buffer, index=False, encoding="utf-8")
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def export_to_excel(report: DefectDetailedReport) -> bytes:
        """
        Export detailed report to Excel (.xlsx) format.

        Returns:
            Excel file as bytes
        """
        # Convert to DataFrame
        data = [defect.model_dump() for defect in report.defects]
        df = pd.DataFrame(data)

        # Convert UUID columns to strings
        uuid_columns = ["id", "project_id", "author_id", "assignee_id"]
        for col in uuid_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # Export to Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Defects Report")

        buffer.seek(0)
        return buffer.getvalue()
