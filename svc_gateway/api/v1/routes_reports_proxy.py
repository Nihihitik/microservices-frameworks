from datetime import date
from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from api.deps import get_current_user_from_token
from core.config import settings

router = APIRouter(prefix="/reports", tags=["Reports Proxy"])


async def proxy_to_reports(
    request: Request,
    method: str,
    path: str,
) -> Any:
    """
    Helper function to proxy requests to svc_reports.

    Args:
        request: FastAPI Request object
        method: HTTP method (GET)
        path: Path to append to REPORTS_SERVICE_URL

    Returns:
        Response from svc_reports

    Raises:
        HTTPException: If service is unavailable or returns error
    """
    headers = {}

    # Add X-Request-ID if available
    if hasattr(request.state, "request_id"):
        headers["X-Request-ID"] = request.state.request_id

    # Add Authorization header (required for all reports endpoints)
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    target_url = f"{settings.REPORTS_SERVICE_URL}{path}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:  # Longer timeout for reports
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                params=request.query_params,
            )
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Reports service timeout",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reports service unavailable",
        )


# ==================== ALL ENDPOINTS ARE PROTECTED ====================


@router.get("/summary")
async def get_summary_report_proxy(
    request: Request,
    project_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for getting summary statistics report (protected endpoint).

    GET /api/v1/reports/summary
    Requires: JWT token (MANAGER, ADMIN, SUPERVISOR, CUSTOMER roles checked by svc_reports)

    Returns aggregated statistics:
    - Total defects count
    - Distribution by status and priority
    - Average resolution time
    """
    return await proxy_to_reports(request, "GET", "/api/v1/reports/summary")


@router.get("/detailed")
async def get_detailed_report_proxy(
    request: Request,
    project_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for getting detailed tabular report (protected endpoint).

    GET /api/v1/reports/detailed
    Requires: JWT token (MANAGER, ADMIN, SUPERVISOR, CUSTOMER roles checked by svc_reports)

    Returns full defect list with enriched data:
    - Project names
    - Resolution times
    - All defect details
    """
    return await proxy_to_reports(request, "GET", "/api/v1/reports/detailed")


@router.get("/export")
async def export_report_proxy(
    request: Request,
    format: str = Query(..., description="Export format: csv or xlsx"),
    project_id: Optional[UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for exporting report as CSV or Excel file (protected endpoint).

    GET /api/v1/reports/export?format=csv
    GET /api/v1/reports/export?format=xlsx
    Requires: JWT token (MANAGER, ADMIN, SUPERVISOR, CUSTOMER roles checked by svc_reports)

    Returns: File download (StreamingResponse)

    Note: Export is limited to 5000 rows maximum by svc_reports
    """
    headers = {}

    # Add X-Request-ID if available
    if hasattr(request.state, "request_id"):
        headers["X-Request-ID"] = request.state.request_id

    # Add Authorization header
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    target_url = f"{settings.REPORTS_SERVICE_URL}/api/v1/reports/export"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:  # Longer timeout for export
            response = await client.get(
                url=target_url,
                headers=headers,
                params=request.query_params,
            )

            # If error response (not 200), return JSON error
            if response.status_code != 200:
                return response.json()

            # Stream the file content
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            content_disposition = response.headers.get("Content-Disposition", "attachment")

            return StreamingResponse(
                content=iter([response.content]),
                media_type=content_type,
                headers={"Content-Disposition": content_disposition},
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Reports service timeout during export",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reports service unavailable",
        )
