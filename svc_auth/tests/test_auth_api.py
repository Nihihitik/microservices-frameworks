from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

try:
    from svc_auth.models.users import Users  # type: ignore
except ModuleNotFoundError:
    from models.users import Users


def _register_user(client, email="user@example.com", password="Secret123!", role="engineer"):
    payload = {
        "full_name": "Test User",
        "email": email,
        "password": password,
        "role": role,
        "is_active": True,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()["data"]


def test_register_creates_user(client, db_session: Session):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "Secure123!",
            "role": "admin",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "jane@example.com"

    stored = db_session.query(Users).filter(Users.email == "jane@example.com").first()
    assert stored is not None
    assert stored.full_name == "Jane Doe"


def test_register_duplicate_email_returns_400(client):
    _register_user(client, email="dup@example.com")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Dup User",
            "email": "dup@example.com",
            "password": "Another123!",
            "role": "engineer",
            "is_active": True,
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Email already registered"


def test_login_returns_jwt_token(client):
    _register_user(client, email="auth@example.com", password="Secret123!")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "auth@example.com", "password": "Secret123!"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "access_token" in payload["data"]
    assert payload["data"]["token_type"] == "bearer"


def test_login_fails_for_invalid_credentials(client):
    _register_user(client, email="wrong-pass@example.com", password="Secret123!")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong-pass@example.com", "password": "BadPassword"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
