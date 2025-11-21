from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.auth import decode_access_token
from db.database import get_db
from models.users import Role, Users

# OAuth2 scheme для Authorization: Bearer <token>
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Users:
    """
    Dependency для получения текущего пользователя из JWT токена.

    Использование:
        @app.get("/me")
        def get_me(current_user: Users = Depends(get_current_user)):
            return current_user

    Raises:
        HTTPException 401: Если токен невалиден
        HTTPException 404: Если пользователь не найден
        HTTPException 403: Если пользователь неактивен
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = UUID(payload.get("sub"))

    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive"
        )

    return user


def require_role(*allowed_roles: Role):
    """
    Dependency factory для проверки роли пользователя.

    Использование:
        @app.get("/admin/users")
        def admin_users(
            current_user: Users = Depends(require_role(Role.ADMIN, Role.SUPERVISOR))
        ):
            # Только ADMIN и SUPERVISOR могут зайти сюда
            ...

    Args:
        *allowed_roles: Список разрешенных ролей

    Returns:
        Dependency function
    """

    def role_checker(current_user: Users = Depends(get_current_user)) -> Users:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker
