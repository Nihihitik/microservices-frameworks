from uuid import uuid4

import pytest
from fastapi import status

try:
    from svc_defects.api import deps  # type: ignore
    from svc_defects.api.v1 import defects as defects_router  # type: ignore
    from svc_defects.main import app  # type: ignore
    from svc_defects.models.defect_history import DefectHistory  # type: ignore
    from svc_defects.models.defects import (  # type: ignore
        DefectPriority,
        DefectStatus,
        Defects,
    )
except ModuleNotFoundError:
    from api import deps
    from api.v1 import defects as defects_router
    from main import app
    from models.defect_history import DefectHistory
    from models.defects import (
        DefectPriority,
        DefectStatus,
        Defects,
    )


@pytest.fixture(autouse=True)
def stub_external_validations(monkeypatch):
    """Avoid real HTTP calls for related services."""

    async def _stub_validate_project(project_id, token):
        assert token == "stub-token"
        return True

    async def _stub_validate_user(user_id, token):
        return True

    monkeypatch.setattr(defects_router, "validate_project_exists", _stub_validate_project)
    monkeypatch.setattr(defects_router, "validate_user_exists", _stub_validate_user)


def _set_current_user(role: str, user_id):
    app.dependency_overrides[deps.get_current_user_from_token] = (
        lambda: {"user_id": user_id, "role": role}
    )


def test_create_defect_persists_and_tracks_history(client, db_session):
    current_user = uuid4()
    project_id = uuid4()
    assignee_id = uuid4()
    _set_current_user("ENGINEER", current_user)

    payload = {
        "project_id": str(project_id),
        "title": "Cracked column",
        "description": "Visible crack on level 2",
        "priority": DefectPriority.HIGH.value,
        "status": DefectStatus.NEW.value,
        "assignee_id": str(assignee_id),
        "due_date": "2024-12-01",
        "location": "Building A",
        "author_id": str(current_user),
    }

    response = client.post(
        "/api/v1/defects/",
        json=payload,
        headers={"Authorization": "Bearer stub-token"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()["data"]
    assert data["title"] == "Cracked column"

    stored = db_session.query(Defects).filter(Defects.title == "Cracked column").first()
    assert stored is not None
    assert stored.author_id == current_user
    assert stored.assignee_id == assignee_id

    history = (
        db_session.query(DefectHistory)
        .filter(DefectHistory.defect_id == stored.id)
        .all()
    )
    assert len(history) == 1
    assert history[0].field_name == "created"
