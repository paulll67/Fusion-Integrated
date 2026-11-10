from modules.leave.api import urls
from modules.leave.registry import PERMISSIONS
from modules.leave.schedule import BEAT_SCHEDULE


def _names():
    return {pattern.name for pattern in urls.urlpatterns}


def test_uc_primary_request_and_review_routes_exist():
    assert {"requests", "request-detail", "request-decision", "tasks", "task-detail"} <= _names()


def test_uc_final_decision_permissions_are_separate():
    codes = {code for code, _ in PERMISSIONS}
    assert "leave.request.review" in codes
    assert "leave.request.approve" in codes
    assert "leave.request.review" != "leave.request.approve"


def test_uc_lifecycle_detail_surface_exists():
    assert "request-detail" in _names()
    assert "request-decision" in _names()


def test_uc_resumption_surface_exists():
    assert "resumptions" in _names()
    assert "leave.resumption.create" in {code for code, _ in PERMISSIONS}


def test_uc_balance_history_and_export_surfaces_exist():
    names = _names()
    assert {"balances", "history", "export"} <= names


def test_uc_admin_and_event_surfaces_exist():
    names = _names()
    assert {"policy", "hierarchy", "calendar", "offline", "sla"} <= names
    assert {"leave.process_year_end", "leave.process_sla_thresholds"} <= set(BEAT_SCHEDULE)
