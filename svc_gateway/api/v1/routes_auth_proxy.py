from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from api.deps import get_current_user_from_token
from core.config import settings

router = APIRouter(tags=["Auth Proxy"])


async def proxy_to_auth(
    request: Request,
    method: str,
    path: str,
    body: Optional[dict] = None,
    auth_required: bool = True,
) -> Any:
    """
    Helper function to proxy requests to svc_auth.

    Args:
        request: FastAPI Request object
        method: HTTP method (GET, POST, PATCH, etc.)
        path: Path to append to AUTH_SERVICE_URL
        body: Optional request body (for POST/PATCH)
        auth_required: Whether to include Authorization header

    Returns:
        Response from svc_auth

    Raises:
        HTTPException: If service is unavailable or returns error
    """
    headers = {}

    # Add X-Request-ID if available
    if hasattr(request.state, "request_id"):
        headers["X-Request-ID"] = request.state.request_id

    # Add Authorization header if auth is required
    if auth_required and "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    target_url = f"{settings.AUTH_SERVICE_URL}{path}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                json=body,
                params=request.query_params,
            )
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Auth service timeout",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable",
        )


# ==================== PUBLIC ENDPOINTS ====================


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register_proxy(request: Request, body: dict):
    """
    Proxy for user registration (public endpoint).

    POST /api/v1/auth/register
    """
    return await proxy_to_auth(request, "POST", "/api/v1/auth/register", body, auth_required=False)


@router.post("/auth/login")
async def login_proxy(request: Request, body: dict):
    """
    Proxy for user login (public endpoint).

    POST /api/v1/auth/login
    """
    return await proxy_to_auth(request, "POST", "/api/v1/auth/login", body, auth_required=False)


# ==================== PROTECTED ENDPOINTS ====================


@router.get("/users/me")
async def get_current_user_proxy(
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for getting current user profile (protected endpoint).

    GET /api/v1/users/me
    Requires: JWT token
    """
    return await proxy_to_auth(request, "GET", "/api/v1/users/me")


@router.patch("/users/me")
async def update_current_user_proxy(
    request: Request,
    body: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for updating current user profile (protected endpoint).

    PATCH /api/v1/users/me
    Requires: JWT token
    """
    return await proxy_to_auth(request, "PATCH", "/api/v1/users/me", body)


@router.get("/users/")
async def list_users_proxy(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for listing users with filters (protected endpoint).

    GET /api/v1/users/
    Requires: JWT token (ADMIN or SUPERVISOR role checked by svc_auth)
    """
    return await proxy_to_auth(request, "GET", "/api/v1/users/")


@router.get("/users/{user_id}")
async def get_user_by_id_proxy(
    request: Request,
    user_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for getting user by ID (protected endpoint).

    GET /api/v1/users/{user_id}
    Requires: JWT token (ADMIN or SUPERVISOR role checked by svc_auth)
    """
    return await proxy_to_auth(request, "GET", f"/api/v1/users/{user_id}")
