from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.auth import decode_access_token

security = HTTPBearer()


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Extract user_id and role from JWT token.

    Returns:
        dict with fields:
            - user_id: UUID of the user
            - role: str user role (ENGINEER, MANAGER, SUPERVISOR, CUSTOMER, ADMIN)
            - token: str JWT token (for inter-service calls)

    Raises:
        HTTPException 401: If token is invalid
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = UUID(payload.get("sub"))
    role = payload.get("role")

    return {"user_id": user_id, "role": role, "token": token}


def require_role(*allowed_roles: str):
    """
    Dependency factory for checking user role.

    Usage:
        @app.get("/reports")
        def get_reports(
            _role_check = Depends(require_role("MANAGER", "SUPERVISOR"))
        ):
            # Only MANAGER and SUPERVISOR can access
            ...

    Args:
        *allowed_roles: List of allowed roles (strings)

    Returns:
        Dependency function

    Raises:
        HTTPException 403: If user role is not in allowed_roles
    """

    def role_checker(current_user: dict = Depends(get_current_user_from_token)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}",
            )
        return current_user

    return role_checker
