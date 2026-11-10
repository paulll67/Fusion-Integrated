from pathlib import Path

from config.celery import app
from modules.leave.models import LeaveRequest, WorkflowTask
from modules.leave.registry import ROLE_GRANTS
from modules.leave.schedule import BEAT_SCHEDULE, TASK_ROUTES


ROOT = Path(__file__).resolve().parents[3]


def test_wf_substitute_path_surface_exists():
    assert {"substitute_user_id", "has_substitute"} <= {
        field.name for field in LeaveRequest._meta.fields
    }
    assert "leave.workflow_task.view" in ROLE_GRANTS["unit_head"]


def test_wf_higher_sanction_and_director_permissions_exist():
    assert "leave.request.review" in ROLE_GRANTS["sanctioning_authority"]
    assert "leave.request.approve" in ROLE_GRANTS["sanctioning_authority"]


def test_wf_cancellation_surface_exists():
    fields = {field.name for field in LeaveRequest._meta.fields}
    assert {"status", "is_cancelled", "cancelled_at"} <= fields


def test_wf_extension_task_controls_exist():
    fields = {field.name for field in WorkflowTask._meta.fields}
    assert {"request_id", "task_kind", "assigned_user_id", "state"} <= fields
    assert "leave.workflow_task.update" in ROLE_GRANTS["unit_head"]


def test_wf_resumption_review_surface_exists():
    assert "resumption" in (ROOT / "modules/leave/api/urls.py").read_text()


def test_wf_composite_schedule_is_registered():
    expected = {
        "leave.process_year_end",
        "leave.process_sla_thresholds",
        "leave.send_sla_reminders",
    }
    assert expected <= set(BEAT_SCHEDULE)
    assert expected <= set(app.tasks)
    assert expected <= set(TASK_ROUTES)
