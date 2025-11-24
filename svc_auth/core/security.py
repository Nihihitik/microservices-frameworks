import os

from passlib.context import CryptContext

os.environ.setdefault("PASSLIB_BCRYPT_TRUNCATE_ERROR", "1")
os.environ.setdefault("PASSLIB_BCRYPT_DETECT_WRAPAROUND", "0")

# Контекст для хеширования паролей (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt.

    Args:
        password: Plaintext пароль

    Returns:
        Хешированный пароль
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие plaintext пароля его хешу.

    Args:
        plain_password: Введенный пользователем пароль
        hashed_password: Сохраненный хеш из БД

    Returns:
        True если пароль верный, False иначе
    """
    return pwd_context.verify(plain_password, hashed_password)
