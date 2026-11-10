from pathlib import Path

from modules.leave.api import urls
from modules.leave.api.serializers import LeaveRequestSerializer
from modules.leave.registry import PERMISSIONS, ROLE_GRANTS
from modules.leave.schedule import BEAT_SCHEDULE, TASK_ROUTES


ROOT = Path(__file__).resolve().parents[3]


def test_fr_registry_permission_catalog_is_complete():
    codes = {code for code, _ in PERMISSIONS}
    assert "leave.request.view" in codes
    assert "leave.request.create" in codes
    assert "leave.request.export" in codes
    assert "leave.workflow_task.update" in codes
    assert "leave.calendar.publish" in codes
    assert "leave.sla.manage" in codes
    assert all(set(grants) <= codes for grants in ROLE_GRANTS.values())


def test_fr_serializer_rejects_invalid_category_and_dates():
    serializer = LeaveRequestSerializer(
        data={
            "category": "INVALID",
            "start_date": "2026-12-10",
            "end_date": "2026-12-01",
        }
    )
    assert serializer.is_valid() is False
    assert "non_field_errors" in serializer.errors or "category" in serializer.errors


def test_fr_scoping_uses_ownership_and_staff_grants():
    source = (ROOT / "modules/leave/selectors/scoping.py").read_text()
    assert 'base.filter(user_id=user_id)' in source
    assert '"leave.request.review"' in source
    assert '"leave.workflow_task.update"' in source


def test_fr_required_api_surfaces_are_registered():
    names = {pattern.name for pattern in urls.urlpatterns}
    assert {"requests", "request-detail", "request-decision", "export"} <= names


def test_fr_administrative_permissions_are_registered():
    codes = {code for code, _ in PERMISSIONS}
    assert {"leave.policy.manage", "leave.hierarchy.manage", "leave.record.manage"} <= codes


def test_fr_scheduled_sla_entry_points_are_registered():
    assert "leave.process_sla_thresholds" in BEAT_SCHEDULE
    assert "leave.send_sla_reminders" in BEAT_SCHEDULE
    assert TASK_ROUTES["leave.process_sla_thresholds"]["queue"] == "notifications"
