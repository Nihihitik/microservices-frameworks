from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException, status

from core.config import settings
from models.users import Role


def create_access_token(user_id: UUID, role: Role) -> str:
    """
    !>7405B JWT access token.

    Args:
        user_id: UUID ?>;L7>20B5;O
        role:  >;L ?>;L7>20B5;O (ENGINEER, ADMIN, etc.)

    Returns:
        JWT B>:5= 2 2845 AB@>:8
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),  # UUID ’ string 4;O JSON
        "role": role.value,  # Enum ’ string
        "exp": int(expire.timestamp()),
    }

    encoded_jwt = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    5:>48@C5B 8 20;848@C5B JWT B>:5=.

    Args:
        token: JWT AB@>:0

    Returns:
        Payload B>:5=0 (dict A sub, role, exp)

    Raises:
        HTTPException 401: A;8 B>:5= =520;845= 8;8 8AB5:
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
