from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from core.config import settings


def decode_access_token(token: str) -> dict:
    """
    Декодирует и валидирует JWT токен.

    Args:
        token: JWT строка

    Returns:
        Payload токена (dict с sub, role, exp)

    Raises:
        HTTPException 401: Если токен невалиден или истек
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
