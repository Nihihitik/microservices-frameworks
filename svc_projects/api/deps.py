from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.auth import decode_access_token
from core.config import settings
from db.database import get_db

# OAuth2 scheme для Authorization: Bearer <token>
security = HTTPBearer()


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Извлекает user_id и role из JWT токена.

    Использование:
        @app.get("/projects")
        def get_projects(current_user: dict = Depends(get_current_user_from_token)):
            user_id = current_user["user_id"]
            role = current_user["role"]

    Returns:
        dict с полями:
            - user_id: UUID пользователя
            - role: str роль пользователя (ENGINEER, MANAGER, SUPERVISOR, CUSTOMER)

    Raises:
        HTTPException 401: Если токен невалиден
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = UUID(payload.get("sub"))
    role = payload.get("role")

    return {"user_id": user_id, "role": role}


def require_role(*allowed_roles: str):
    """
    Dependency factory для проверки роли пользователя.

    Использование:
        @app.post("/projects")
        def create_project(
            _role_check = Depends(require_role("MANAGER", "ADMIN"))
        ):
            # Только MANAGER и ADMIN могут создавать проекты
            ...

    Args:
        *allowed_roles: Список разрешенных ролей (строки)

    Returns:
        Dependency function
    """

    def role_checker(current_user: dict = Depends(get_current_user_from_token)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}",
            )
        return current_user

    return role_checker


async def validate_manager_exists(manager_id: UUID, token: str) -> bool:
    """
    Проверяет существование пользователя через HTTP запрос к svc_auth.

    Args:
        manager_id: UUID пользователя для проверки
        token: JWT токен для авторизации запроса

    Returns:
        True если пользователь существует

    Raises:
        HTTPException 404: Если пользователь не найден
        HTTPException 503: Если сервис auth недоступен
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/api/v1/users/{manager_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {manager_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service error"
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service timeout"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Authentication service unavailable: {str(e)}"
        )
