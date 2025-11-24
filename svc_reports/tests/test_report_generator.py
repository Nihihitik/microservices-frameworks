from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

try:
    from svc_reports.services.report_generator import ReportGenerator  # type: ignore
    from svc_reports.schemas.reports import DefectPriority, DefectStatus  # type: ignore
except ModuleNotFoundError:
    from services.report_generator import ReportGenerator
    from schemas.reports import DefectPriority, DefectStatus


def _make_defect(status=DefectStatus.NEW, priority=DefectPriority.MEDIUM, days_ago=1):
    defect_id = uuid4()
    project_id = uuid4()
    created = datetime.now(timezone.utc) - timedelta(days=days_ago)
    updated = created + timedelta(days=days_ago)
    return {
        "id": str(defect_id),
        "project_id": str(project_id),
        "title": "Sample",
        "priority": priority.value,
        "status": status.value,
        "author_id": str(uuid4()),
        "assignee_id": str(uuid4()),
        "due_date": created.date().isoformat(),
        "created_at": created.isoformat(),
        "updated_at": updated.isoformat(),
    }


def test_filter_by_date_range_returns_only_matching_items():
    defects = [
        _make_defect(days_ago=10),
        _make_defect(days_ago=5),
        _make_defect(days_ago=1),
    ]
    start = date.today() - timedelta(days=6)
    end = date.today() - timedelta(days=2)

    filtered = ReportGenerator.filter_by_date_range(defects, start, end)

    assert len(filtered) == 1
    assert filtered[0]["title"] == "Sample"


def test_generate_summary_report_counts_statuses_and_priorities():
    defects = [
        _make_defect(status=DefectStatus.NEW, priority=DefectPriority.HIGH),
        _make_defect(status=DefectStatus.CLOSED, priority=DefectPriority.LOW),
        _make_defect(status=DefectStatus.CLOSED, priority=DefectPriority.LOW),
    ]

    report = ReportGenerator.generate_summary_report(defects=defects, project=None, filters={"status": "all"})

    assert report.total_defects == 3
    assert report.closed_defects_count == 2
    assert report.open_defects_count == 1
    assert any(item.status == DefectStatus.NEW for item in report.status_distribution)
    assert any(item.priority == DefectPriority.LOW for item in report.priority_distribution)
