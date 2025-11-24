from uuid import uuid4

import pytest
from fastapi import HTTPException

try:
    from svc_auth.core.auth import create_access_token, decode_access_token  # type: ignore
    from svc_auth.core.security import hash_password, verify_password  # type: ignore
    from svc_auth.models.users import Role  # type: ignore
except ModuleNotFoundError:
    from core.auth import create_access_token, decode_access_token
    from core.security import hash_password, verify_password
    from models.users import Role


def test_create_and_decode_access_token_success():
    user_id = uuid4()
    token = create_access_token(user_id=user_id, role=Role.ADMIN)

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == Role.ADMIN.value
    assert "exp" in payload


def test_decode_access_token_invalid_token():
    with pytest.raises(HTTPException) as exc:
        decode_access_token("invalid.token.value")

    assert exc.value.status_code == 401
    assert "Invalid token" in exc.value.detail


def test_password_hashing_and_verification():
    raw_password = "Sup3rSecure!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("wrong-pass", hashed) is False
