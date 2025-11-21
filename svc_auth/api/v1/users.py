from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, require_role
from core.security import hash_password
from db.database import get_db
from models.users import Role, Users
from schemas import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=dict)
def get_current_user_profile(current_user: Users = Depends(get_current_user)):
    """
    Получение профиля текущего пользователя.

    Требуется: валидный JWT токен

    Returns:
        {"success": true, "data": {...}}
    """
    return {"success": True, "data": UserRead.model_validate(current_user)}


@router.patch("/me", response_model=dict)
def update_current_user_profile(
    update_data: UserUpdate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Обновление профиля текущего пользователя.

    Пользователи могут обновлять только:
    - full_name
    - email (с проверкой уникальности)
    - password

    НЕ могут менять: role, is_active (только админы)
    """
    # Обновление разрешенных полей
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name

    if update_data.email is not None:
        # Проверка уникальности нового email
        existing = (
            db.query(Users)
            .filter(Users.email == update_data.email, Users.id != current_user.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
            )
        current_user.email = update_data.email

    if update_data.password is not None:
        current_user.hash_password = hash_password(update_data.password)

    # Запрет на изменение роли и активности для обычных пользователей
    if update_data.role is not None or update_data.is_active is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify role or active status via /me endpoint",
        )

    db.commit()
    db.refresh(current_user)

    return {"success": True, "data": UserRead.model_validate(current_user)}


@router.get("/", response_model=dict)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Role | None = None,
    is_active: bool | None = None,
    current_user: Users = Depends(require_role(Role.ADMIN, Role.SUPERVISOR)),
    db: Session = Depends(get_db),
):
    """
    Список пользователей с фильтрацией и пагинацией.

    Доступно только: ADMIN, SUPERVISOR

    Query параметры:
    - skip: смещение (для пагинации)
    - limit: количество (max 1000)
    - role: фильтр по роли
    - is_active: фильтр по активности
    """
    query = db.query(Users)

    if role is not None:
        query = query.filter(Users.role == role)

    if is_active is not None:
        query = query.filter(Users.is_active == is_active)

    users = query.offset(skip).limit(limit).all()

    return {"success": True, "data": [UserRead.model_validate(u) for u in users]}


@router.get("/{user_id}", response_model=dict)
def get_user_by_id(
    user_id: UUID,
    current_user: Users = Depends(require_role(Role.ADMIN, Role.SUPERVISOR)),
    db: Session = Depends(get_db),
):
    """
    Получение конкретного пользователя по ID.

    Доступно только: ADMIN, SUPERVISOR
    """
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return {"success": True, "data": UserRead.model_validate(user)}
