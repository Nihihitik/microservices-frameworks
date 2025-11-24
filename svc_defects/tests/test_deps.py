import pytest
from fastapi import HTTPException

try:
    from svc_defects.api.deps import check_valid_status_transition  # type: ignore
    from svc_defects.models.defects import DefectStatus  # type: ignore
except ModuleNotFoundError:
    from api.deps import check_valid_status_transition
    from models.defects import DefectStatus


def test_check_valid_status_transition_allows_valid_move():
    assert (
        check_valid_status_transition(DefectStatus.NEW, DefectStatus.IN_PROGRESS) is True
    )


def test_check_valid_status_transition_blocks_invalid_move():
    with pytest.raises(HTTPException) as exc:
        check_valid_status_transition(DefectStatus.NEW, DefectStatus.CLOSED)

    assert exc.value.status_code == 400
    assert "Invalid status transition" in exc.value.detail


def test_check_valid_status_transition_blocks_final_state_changes():
    with pytest.raises(HTTPException) as exc:
        check_valid_status_transition(DefectStatus.CLOSED, DefectStatus.IN_PROGRESS)

    assert exc.value.status_code == 400
    assert "final status" in exc.value.detail
