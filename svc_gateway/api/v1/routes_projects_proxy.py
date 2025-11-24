from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from api.deps import get_current_user_from_token
from core.config import settings
from core.http import request_with_retry

router = APIRouter(prefix="/projects", tags=["Projects Proxy"])


async def proxy_to_projects(
    request: Request,
    method: str,
    path: str,
    body: Optional[dict] = None,
) -> Any:
    """
    Helper function to proxy requests to svc_projects.

    Args:
        request: FastAPI Request object
        method: HTTP method (GET, POST, PATCH, etc.)
        path: Path to append to PROJECTS_SERVICE_URL
        body: Optional request body (for POST/PATCH)

    Returns:
        Response from svc_projects

    Raises:
        HTTPException: If service is unavailable or returns error
    """
    headers = {}

    # Add X-Request-ID if available
    if hasattr(request.state, "request_id"):
        headers["X-Request-ID"] = request.state.request_id

    # Add Authorization header (required for all project endpoints)
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    target_url = f"{settings.PROJECTS_SERVICE_URL}{path}"

    try:
        response = await request_with_retry(
            method=method,
            url=target_url,
            headers=headers,
            json=body,
            params=request.query_params,
            timeout=5.0,
        )
        return response.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Projects service timeout",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Projects service unavailable",
        )


# ==================== ALL ENDPOINTS ARE PROTECTED ====================


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project_proxy(
    request: Request,
    body: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for creating a new project (protected endpoint).

    POST /api/v1/projects/
    Requires: JWT token (MANAGER or ADMIN role checked by svc_projects)
    """
    return await proxy_to_projects(request, "POST", "/api/v1/projects/", body)


@router.get("/")
async def get_projects_proxy(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    stage: Optional[str] = None,
    customer_name: Optional[str] = None,
    manager_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for listing projects with filters (protected endpoint).

    GET /api/v1/projects/
    Requires: JWT token
    Auto-filters by manager_id for SUPERVISOR/CUSTOMER roles (done by svc_projects)
    """
    return await proxy_to_projects(request, "GET", "/api/v1/projects/")


@router.get("/{project_id}")
async def get_project_proxy(
    request: Request,
    project_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for getting project details by ID (protected endpoint).

    GET /api/v1/projects/{project_id}
    Requires: JWT token
    """
    return await proxy_to_projects(request, "GET", f"/api/v1/projects/{project_id}")


@router.patch("/{project_id}")
async def update_project_proxy(
    request: Request,
    project_id: UUID,
    body: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for updating a project (protected endpoint).

    PATCH /api/v1/projects/{project_id}
    Requires: JWT token (MANAGER or ADMIN role checked by svc_projects)
    """
    return await proxy_to_projects(request, "PATCH", f"/api/v1/projects/{project_id}", body)
