from datetime import date
from io import BytesIO
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from api.deps import get_current_user_from_token, require_role
from schemas.reports import DefectPriority, DefectStatus, ExportFormat
from services.data_fetcher import DataFetcherService
from services.report_generator import ReportGenerator

router = APIRouter(prefix="/reports", tags=["Reports"])

# Maximum rows for export (as per user decision)
MAX_EXPORT_ROWS = 5000


@router.get("/summary", response_model=dict)
async def get_summary_report(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    start_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date (inclusive)"),
    status: Optional[DefectStatus] = Query(None, description="Filter by defect status"),
    priority: Optional[DefectPriority] = Query(
        None, description="Filter by defect priority"
    ),
    current_user: dict = Depends(get_current_user_from_token),
    _role_check=Depends(require_role("MANAGER", "ADMIN", "SUPERVISOR", "CUSTOMER")),
):
    """
    Get summary statistics report with aggregated metrics.

    Access:
    - MANAGER, ADMIN: See all projects
    - SUPERVISOR, CUSTOMER: See all projects (auto-filtering not implemented yet)

    Returns:
        {"success": True, "data": DefectSummaryReport}
    """
    token = current_user["token"]
    fetcher = DataFetcherService(token)

    # Fetch defects with filters
    defects = await fetcher.fetch_defects(
        project_id=project_id,
        status=status.value if status else None,
        priority=priority.value if priority else None,
    )

    # Apply date range filter (in-memory)
    defects = ReportGenerator.filter_by_date_range(defects, start_date, end_date)

    # Fetch project details if filtered by single project
    project = None
    if project_id:
        project = await fetcher.fetch_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )

    # Generate report
    filters_applied = {
        "project_id": str(project_id) if project_id else None,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "status": status.value if status else None,
        "priority": priority.value if priority else None,
    }

    report = ReportGenerator.generate_summary_report(
        defects=defects, project=project, filters=filters_applied
    )

    return {"success": True, "data": report.model_dump()}


@router.get("/detailed", response_model=dict)
async def get_detailed_report(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    start_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date (inclusive)"),
    status: Optional[DefectStatus] = Query(None, description="Filter by defect status"),
    priority: Optional[DefectPriority] = Query(
        None, description="Filter by defect priority"
    ),
    current_user: dict = Depends(get_current_user_from_token),
    _role_check=Depends(require_role("MANAGER", "ADMIN", "SUPERVISOR", "CUSTOMER")),
):
    """
    Get detailed tabular report with all defects matching filters.

    This endpoint returns full defect list with enriched data (project names, resolution times).
    Useful for client-side rendering of tables/charts.

    Access:
    - MANAGER, ADMIN: See all projects
    - SUPERVISOR, CUSTOMER: See all projects (auto-filtering not implemented yet)

    Returns:
        {"success": True, "data": DefectDetailedReport}
    """
    token = current_user["token"]
    fetcher = DataFetcherService(token)

    # Fetch defects with filters
    defects = await fetcher.fetch_defects(
        project_id=project_id,
        status=status.value if status else None,
        priority=priority.value if priority else None,
    )

    # Apply date range filter
    defects = ReportGenerator.filter_by_date_range(defects, start_date, end_date)

    # Fetch all projects for enrichment (project names)
    projects = await fetcher.fetch_projects()
    projects_map = {UUID(p["id"]): p for p in projects}

    # Generate report
    filters_applied = {
        "project_id": str(project_id) if project_id else None,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "status": status.value if status else None,
        "priority": priority.value if priority else None,
    }

    report = ReportGenerator.generate_detailed_report(
        defects=defects, projects_map=projects_map, filters=filters_applied
    )

    return {"success": True, "data": report.model_dump()}


@router.get("/export")
async def export_report(
    format: ExportFormat = Query(..., description="Export format (csv or xlsx)"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    start_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date (inclusive)"),
    status: Optional[DefectStatus] = Query(None, description="Filter by defect status"),
    priority: Optional[DefectPriority] = Query(
        None, description="Filter by defect priority"
    ),
    current_user: dict = Depends(get_current_user_from_token),
    _role_check=Depends(require_role("MANAGER", "ADMIN", "SUPERVISOR", "CUSTOMER")),
):
    """
    Export detailed report as CSV or Excel file.

    **Important**: Export is limited to 5000 rows maximum. If your filters match more than
    5000 defects, you must apply more specific filters (date range, project, status, priority).

    Access:
    - MANAGER, ADMIN: See all projects
    - SUPERVISOR, CUSTOMER: See all projects (auto-filtering not implemented yet)

    Returns:
        File download (StreamingResponse with CSV or XLSX)

    Raises:
        HTTPException 400: If export exceeds 5000 rows
    """
    token = current_user["token"]
    fetcher = DataFetcherService(token)

    # Fetch defects with filters
    defects = await fetcher.fetch_defects(
        project_id=project_id,
        status=status.value if status else None,
        priority=priority.value if priority else None,
    )

    # Apply date range filter
    defects = ReportGenerator.filter_by_date_range(defects, start_date, end_date)

    # Check export limit (5000 rows)
    if len(defects) > MAX_EXPORT_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export limit exceeded. Found {len(defects)} defects, maximum allowed is {MAX_EXPORT_ROWS}. "
            "Please apply more specific filters (date range, project, status, priority).",
        )

    # Fetch all projects for enrichment
    projects = await fetcher.fetch_projects()
    projects_map = {UUID(p["id"]): p for p in projects}

    # Generate report
    filters_applied = {
        "project_id": str(project_id) if project_id else None,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "status": status.value if status else None,
        "priority": priority.value if priority else None,
    }

    report = ReportGenerator.generate_detailed_report(
        defects=defects, projects_map=projects_map, filters=filters_applied
    )

    # Export based on format
    if format == ExportFormat.CSV:
        file_content = ReportGenerator.export_to_csv(report)
        media_type = "text/csv"
        filename = f"defects_report_{date.today().isoformat()}.csv"
    else:  # EXCEL
        file_content = ReportGenerator.export_to_excel(report)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"defects_report_{date.today().isoformat()}.xlsx"

    return StreamingResponse(
        BytesIO(file_content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
