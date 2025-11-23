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
            - token: str JWT token (for forwarding to downstream services)

    Raises:
        HTTPException 401: If token is invalid
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = UUID(payload.get("sub"))
    role = payload.get("role")

    return {"user_id": user_id, "role": role, "token": token}
