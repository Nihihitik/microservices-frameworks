from typing import Optional
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.auth import decode_access_token
from core.config import settings
from db.database import get_db
from models.defects import DefectStatus

# OAuth2 scheme для Authorization: Bearer <token>
security = HTTPBearer()


def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Извлекает user_id и role из JWT токена.

    Использование:
        @app.get("/defects")
        def get_defects(current_user: dict = Depends(get_current_user_from_token)):
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
        @app.post("/defects")
        def create_defect(
            _role_check = Depends(require_role("ENGINEER", "MANAGER"))
        ):
            # Только ENGINEER и MANAGER могут создавать дефекты
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


async def validate_user_exists(user_id: UUID, token: str) -> bool:
    """
    Проверяет существование пользователя через HTTP запрос к svc_auth.

    Args:
        user_id: UUID пользователя для проверки
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
                f"{settings.AUTH_SERVICE_URL}/api/v1/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
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


async def validate_project_exists(project_id: UUID, token: str) -> bool:
    """
    Проверяет существование проекта через HTTP запрос к svc_projects.

    Args:
        project_id: UUID проекта для проверки
        token: JWT токен для авторизации запроса

    Returns:
        True если проект существует

    Raises:
        HTTPException 404: Если проект не найден
        HTTPException 503: Если сервис projects недоступен
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.PROJECTS_SERVICE_URL}/api/v1/projects/{project_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID {project_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Projects service error"
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Projects service timeout"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Projects service unavailable: {str(e)}"
        )


def check_valid_status_transition(
    current_status: DefectStatus, new_status: DefectStatus
) -> bool:
    """
    Проверяет валидность перехода статуса дефекта.

    Допустимые переходы:
    - NEW → IN_PROGRESS, CANCELED
    - IN_PROGRESS → ON_REVIEW, CANCELED
    - ON_REVIEW → CLOSED, IN_PROGRESS, CANCELED
    - CLOSED → (финальный, нельзя менять)
    - CANCELED → (финальный, нельзя менять)

    Args:
        current_status: Текущий статус дефекта
        new_status: Новый статус для установки

    Returns:
        True если переход валидный

    Raises:
        HTTPException 400: Если переход невалидный
    """
    # Если статус не изменяется, это валидно
    if current_status == new_status:
        return True

    # Финальные статусы нельзя изменять
    if current_status in [DefectStatus.CLOSED, DefectStatus.CANCELED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change status from {current_status.value}. It is a final status."
        )

    # Определяем допустимые переходы
    valid_transitions = {
        DefectStatus.NEW: [DefectStatus.IN_PROGRESS, DefectStatus.CANCELED],
        DefectStatus.IN_PROGRESS: [DefectStatus.ON_REVIEW, DefectStatus.CANCELED],
        DefectStatus.ON_REVIEW: [
            DefectStatus.CLOSED,
            DefectStatus.IN_PROGRESS,
            DefectStatus.CANCELED
        ],
    }

    allowed_statuses = valid_transitions.get(current_status, [])

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {current_status.value} to {new_status.value}. "
                   f"Allowed transitions: {[s.value for s in allowed_statuses]}"
        )

    return True
