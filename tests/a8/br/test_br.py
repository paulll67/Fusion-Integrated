from modules.leave.api.serializers import LeaveRequestSerializer
from modules.leave.models import HolidayRHCalendar, SLAConfig
from modules.leave.registry import PERMISSIONS
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_br_category_and_interval_guards():
    valid = LeaveRequestSerializer(
        data={"category": "CL", "start_date": "2026-12-01", "end_date": "2026-12-02"}
    )
    assert valid.is_valid(), valid.errors
    invalid = LeaveRequestSerializer(
        data={"category": "NOPE", "start_date": "2026-12-02", "end_date": "2026-12-01"}
    )
    assert invalid.is_valid() is False


def test_br_substitute_consent_surface():
    source = LeaveRequestSerializer.Meta.fields
    assert "substitute_user_id" in source
    assert "has_substitute" in source


def test_br_review_and_approval_grants_are_distinct():
    codes = {code for code, _ in PERMISSIONS}
    assert "leave.request.review" in codes
    assert "leave.request.approve" in codes


def test_br_cancellation_lifecycle_fields_exist():
    fields = {field.name for field in __import__("modules.leave.models", fromlist=["LeaveRequest"]).LeaveRequest._meta.fields}
    assert {"is_cancelled", "cancelled_at", "status"} <= fields


def test_br_calendar_and_sla_configuration_surface():
    assert {"is_published", "effective_from", "restricted_holidays"} <= {
        field.name for field in HolidayRHCalendar._meta.fields
    }
    assert {"reminder_threshold_hours", "escalation_threshold_hours", "escalation_action"} <= {
        field.name for field in SLAConfig._meta.fields
    }
    assert "def process_sla_thresholds" in (ROOT / "modules/leave/services/sla.py").read_text()
    assert "def process_year_end" in (ROOT / "modules/leave/services/year_end.py").read_text()


def test_br_withdrawal_audit_and_record_surfaces_exist():
    codes = {code for code, _ in PERMISSIONS}
    assert {"leave.request.revoke", "leave.history.view", "leave.record.manage"} <= codes
