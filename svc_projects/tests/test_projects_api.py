from uuid import uuid4

import pytest
from fastapi import status

try:
    from svc_projects.api import deps  # type: ignore
    from svc_projects.api.v1 import projects as projects_router  # type: ignore
    from svc_projects.models.projects import ProjectStage, ProjectStatus, Projects  # type: ignore
    from svc_projects.main import app  # type: ignore
except ModuleNotFoundError:
    from api import deps
    from api.v1 import projects as projects_router
    from models.projects import ProjectStage, ProjectStatus, Projects
    from main import app


@pytest.fixture(autouse=True)
def stub_manager_validation(monkeypatch):
    """Avoid real HTTP calls when validating manager IDs."""

    async def _stub_validate_manager_exists(manager_id, token):
        assert manager_id is not None
        assert token == "stub-token"
        return True

    monkeypatch.setattr(
        projects_router, "validate_manager_exists", _stub_validate_manager_exists
    )


def _set_current_user_override(role: str, user_id):
    app.dependency_overrides[deps.get_current_user_from_token] = (
        lambda: {"user_id": user_id, "role": role}
    )


def test_create_project_success(client, db_session):
    manager_id = uuid4()
    _set_current_user_override("MANAGER", manager_id)

    payload = {
        "name": "Airport Terminal",
        "code": "PRJ-001",
        "address": "1 Aviation Blvd",
        "customer_name": "City Build Corp",
        "stage": ProjectStage.DESIGN.value,
        "status": ProjectStatus.ACTIVE.value,
        "manager_id": str(manager_id),
        "start_date": "2024-01-01",
        "end_date": None,
    }

    response = client.post(
        "/api/v1/projects/",
        json=payload,
        headers={"Authorization": "Bearer stub-token"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Airport Terminal"

    stored = db_session.query(Projects).filter(Projects.code == "PRJ-001").first()
    assert stored is not None
    assert stored.manager_id == manager_id


def test_get_projects_filters_for_supervisor(client, db_session):
    allowed_manager = uuid4()
    other_manager = uuid4()

    project_allowed = Projects(
        name="Allowed Project",
        code="ALLOW",
        address="Addr 1",
        customer_name="Client 1",
        stage=ProjectStage.DESIGN,
        status=ProjectStatus.ACTIVE,
        manager_id=allowed_manager,
    )
    project_denied = Projects(
        name="Hidden Project",
        code="HIDE",
        address="Addr 2",
        customer_name="Client 2",
        stage=ProjectStage.CONSTRUCTION,
        status=ProjectStatus.ON_HOLD,
        manager_id=other_manager,
    )
    db_session.add_all([project_allowed, project_denied])
    db_session.commit()

    _set_current_user_override("SUPERVISOR", allowed_manager)

    response = client.get(
        "/api/v1/projects/",
        headers={"Authorization": "Bearer stub-token"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Allowed Project"
