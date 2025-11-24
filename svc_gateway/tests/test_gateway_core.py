from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

try:
    from svc_gateway.api import deps  # type: ignore
    from svc_gateway.core import auth as gateway_auth  # type: ignore
except ModuleNotFoundError:
    from api import deps
    from core import auth as gateway_auth


def test_request_id_middleware_sets_header(client):
    response = client.get("/")

    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) > 10


def test_get_current_user_from_token_propagates_invalid_token(monkeypatch):
    def fake_decode(_token):
        raise HTTPException(status_code=401, detail="bad token")

    monkeypatch.setattr(gateway_auth, "decode_access_token", fake_decode)

    creds = SimpleNamespace(credentials="bad")

    with pytest.raises(HTTPException) as exc:
        deps.get_current_user_from_token(credentials=creds)

    assert exc.value.status_code == 401
