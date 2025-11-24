from typing import Any, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from api.deps import get_current_user_from_token
from core.config import settings
from core.http import request_with_retry

router = APIRouter(tags=["Defects Proxy"])


async def proxy_to_defects(
    request: Request,
    method: str,
    path: str,
    body: Optional[dict] = None,
) -> Any:
    """
    Helper function to proxy requests to svc_defects.

    Args:
        request: FastAPI Request object
        method: HTTP method (GET, POST, PATCH, DELETE, etc.)
        path: Path to append to DEFECTS_SERVICE_URL
        body: Optional request body (for POST/PATCH)

    Returns:
        Response from svc_defects

    Raises:
        HTTPException: If service is unavailable or returns error
    """
    headers = {}

    # Add X-Request-ID if available
    if hasattr(request.state, "request_id"):
        headers["X-Request-ID"] = request.state.request_id

    # Add Authorization header (required for all defects endpoints)
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    target_url = f"{settings.DEFECTS_SERVICE_URL}{path}"

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
            detail="Defects service timeout",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Defects service unavailable",
        )


# ==================== DEFECTS ENDPOINTS ====================


@router.post("/defects/", status_code=status.HTTP_201_CREATED)
async def create_defect_proxy(
    request: Request,
    body: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for creating a new defect (protected endpoint).

    POST /api/v1/defects/
    Requires: JWT token
    """
    return await proxy_to_defects(request, "POST", "/api/v1/defects/", body)


@router.get("/defects/")
async def get_defects_proxy(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    author_id: Optional[UUID] = None,
    assignee_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for listing defects with filters (protected endpoint).

    GET /api/v1/defects/
    Requires: JWT token
    """
    return await proxy_to_defects(request, "GET", "/api/v1/defects/")


@router.get("/defects/{defect_id}")
async def get_defect_proxy(
    request: Request,
    defect_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for getting defect details by ID (protected endpoint).

    GET /api/v1/defects/{defect_id}
    Requires: JWT token
    """
    return await proxy_to_defects(request, "GET", f"/api/v1/defects/{defect_id}")


@router.patch("/defects/{defect_id}")
async def update_defect_proxy(
    request: Request,
    defect_id: UUID,
    body: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for updating a defect (protected endpoint).

    PATCH /api/v1/defects/{defect_id}
    Requires: JWT token (ENGINEER can edit own, MANAGER/ADMIN can edit all)
    """
    return await proxy_to_defects(request, "PATCH", f"/api/v1/defects/{defect_id}", body)


@router.delete("/defects/{defect_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_defect_proxy(
    request: Request,
    defect_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for deleting a defect (protected endpoint).

    DELETE /api/v1/defects/{defect_id}
    Requires: JWT token (MANAGER or ADMIN role checked by svc_defects)
    """
    return await proxy_to_defects(request, "DELETE", f"/api/v1/defects/{defect_id}")


@router.get("/defects/{defect_id}/history")
async def get_defect_history_proxy(
    request: Request,
    defect_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for getting defect change history (protected endpoint).

    GET /api/v1/defects/{defect_id}/history
    Requires: JWT token
    """
    return await proxy_to_defects(request, "GET", f"/api/v1/defects/{defect_id}/history")


# ==================== COMMENTS ENDPOINTS ====================


@router.post("/comments/", status_code=status.HTTP_201_CREATED)
async def create_comment_proxy(
    request: Request,
    body: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for creating a comment on a defect (protected endpoint).

    POST /api/v1/comments/
    Requires: JWT token
    """
    return await proxy_to_defects(request, "POST", "/api/v1/comments/", body)


@router.get("/comments/defects/{defect_id}/comments")
async def get_comments_proxy(
    request: Request,
    defect_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for getting all comments for a defect (protected endpoint).

    GET /api/v1/comments/defects/{defect_id}/comments
    Requires: JWT token
    """
    return await proxy_to_defects(request, "GET", f"/api/v1/comments/defects/{defect_id}/comments")


@router.patch("/comments/{comment_id}")
async def update_comment_proxy(
    request: Request,
    comment_id: UUID,
    body: dict,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for updating a comment (protected endpoint).

    PATCH /api/v1/comments/{comment_id}
    Requires: JWT token (can only edit own comments, checked by svc_defects)
    """
    return await proxy_to_defects(request, "PATCH", f"/api/v1/comments/{comment_id}", body)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_proxy(
    request: Request,
    comment_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for deleting a comment (protected endpoint).

    DELETE /api/v1/comments/{comment_id}
    Requires: JWT token (can only delete own comments or if MANAGER/ADMIN, checked by svc_defects)
    """
    return await proxy_to_defects(request, "DELETE", f"/api/v1/comments/{comment_id}")


# ==================== ATTACHMENTS ENDPOINTS ====================


@router.post("/attachments/", status_code=status.HTTP_201_CREATED)
async def upload_attachment_proxy(
    request: Request,
    defect_id: UUID = Query(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for uploading an attachment (protected endpoint).

    POST /api/v1/attachments/?defect_id=...
    Requires: JWT token
    Content-Type: multipart/form-data
    """
    headers = {}

    # Add X-Request-ID if available
    if hasattr(request.state, "request_id"):
        headers["X-Request-ID"] = request.state.request_id

    # Add Authorization header
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    target_url = f"{settings.DEFECTS_SERVICE_URL}/api/v1/attachments/"

    try:
        files = {"file": (file.filename, await file.read(), file.content_type)}
        response = await request_with_retry(
            method="POST",
            url=target_url,
            headers=headers,
            files=files,
            params={"defect_id": str(defect_id)},
            timeout=10.0,
        )
        return response.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Defects service timeout during file upload",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Defects service unavailable",
        )


@router.get("/attachments/defects/{defect_id}/attachments")
async def get_attachments_proxy(
    request: Request,
    defect_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for getting all attachments for a defect (protected endpoint).

    GET /api/v1/attachments/defects/{defect_id}/attachments
    Requires: JWT token
    """
    return await proxy_to_defects(request, "GET", f"/api/v1/attachments/defects/{defect_id}/attachments")


@router.get("/attachments/{attachment_id}/download")
async def download_attachment_proxy(
    request: Request,
    attachment_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for downloading an attachment (protected endpoint).

    GET /api/v1/attachments/{attachment_id}/download
    Requires: JWT token
    Returns: Streaming response with file content
    """
    headers = {}

    # Add X-Request-ID if available
    if hasattr(request.state, "request_id"):
        headers["X-Request-ID"] = request.state.request_id

    # Add Authorization header
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    target_url = f"{settings.DEFECTS_SERVICE_URL}/api/v1/attachments/{attachment_id}/download"

    try:
        response = await request_with_retry(
            method="GET",
            url=target_url,
            headers=headers,
            timeout=10.0,
        )

        if response.status_code != 200:
            return response.json()

        return StreamingResponse(
            content=iter([response.content]),
            media_type=response.headers.get("Content-Type", "application/octet-stream"),
            headers={
                "Content-Disposition": response.headers.get(
                    "Content-Disposition", "attachment"
                ),
            },
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Defects service timeout during file download",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Defects service unavailable",
        )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment_proxy(
    request: Request,
    attachment_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Proxy for deleting an attachment (protected endpoint).

    DELETE /api/v1/attachments/{attachment_id}
    Requires: JWT token (MANAGER or ADMIN role checked by svc_defects)
    """
    return await proxy_to_defects(request, "DELETE", f"/api/v1/attachments/{attachment_id}")
