from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth import create_access_token
from core.security import hash_password, verify_password
from db.database import get_db
from models.users import Users
from schemas import Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Схема для логина"""

    email: str
    password: str


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя.

    - Валидация email (уникальность)
    - Хеширование пароля
    - Создание пользователя в БД

    Returns:
        {"success": true, "data": {"id": "...", "email": "..."}}
    """
    # Проверка существования email
    existing_user = db.query(Users).filter(Users.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Создание пользователя
    hashed_pwd = hash_password(user_data.password)

    new_user = Users(
        full_name=user_data.full_name,
        email=user_data.email,
        hash_password=hashed_pwd,
        role=user_data.role,
        is_active=user_data.is_active,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Единый формат ответа
    return {"success": True, "data": UserRead.model_validate(new_user)}


@router.post("/login", response_model=dict)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Аутентификация пользователя и выдача JWT токена.

    Args:
        login_data: Email и пароль пользователя

    Returns:
        {"success": true, "data": {"access_token": "...", "token_type": "bearer"}}

    Raises:
        HTTPException 401: Неверный email или пароль
    """
    user = db.query(Users).filter(Users.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    # Создание JWT токена
    access_token = create_access_token(user.id, user.role)

    return {"success": True, "data": Token(access_token=access_token)}
