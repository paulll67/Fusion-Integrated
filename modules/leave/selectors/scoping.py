"""Role scope, decided in one place (ELM-PC-018).

Every list and detail view starts from a queryset built here. Ownership is
enforced by narrowing the queryset, never by fetching a row and then checking
it — so a row you may not see is a 404, not a 403. A 403 would confirm it
exists, which for leave data is itself a disclosure.

    ELM-PC-BR-009  Unit Head sees only requests in their own unit (if configured)
    ELM-PC-BR-010  TPO / Director sees everything in the module
    ELM-PC-BR-016  Employees get anonymised aggregates, not raw records
    ELM-PC-BR-019  Alumni get a narrow read-only slice (if applicable)
    ELM-PC-BR-020  Alumni are excluded from active workflow objects
    ELM-PC-BR-023  Sensitive data is restricted to authorised readers
"""

from __future__ import annotations

from django.db.models import QuerySet

from modules.directory.models import UserRef
from modules.leave.contracts import EmployeeDTO
from modules.leave.models import (
    LeaveRequest,
    SubstituteAssignment,
    WorkflowTask,
)

# Permission codes. Held by TPO / Director via the IAM.
P_VIEW_ALL = "leave.request.view"
P_MANAGE_TASKS = "leave.workflow_task.update"
P_VIEW_REPORTS = "leave.request.export"

# Any of these makes someone staff; view_self is the employee grant and absent.
STAFF_SCOPE_PERMISSIONS = (
    P_VIEW_ALL,
    "leave.request.review",
    "leave.workflow_task.update",
    "leave.request.export",
)

ALUMNI_ROLE = "alumni"


def _is_recruiter(actor) -> bool:
    # In ELM context, 'recruiter' is not a standard role; treat as generic admin.
    return False


def _own_id(actor) -> int | None:
    """None means no identity to scope by, which resolves to an empty
    queryset. Deny is the only safe reading of 'who is asking?' being
    unanswerable."""
    return getattr(actor, "user_id", None)


def _is_alumni(actor) -> bool:
    """Alumni are an IAM role, not a separate pool."""
    return ALUMNI_ROLE in {r.lower() for r in getattr(actor, "roles", ())}


def _has(actor, *codes: str) -> bool:
    check = getattr(actor, "has_permission", None)
    return bool(check) and any(check(c) for c in codes)


def is_staff(actor) -> bool:
    """Sees the whole module. Never a recruiter or alumnus, whatever
    permissions they might somehow carry."""
    return (
        not _is_recruiter(actor) and not _is_alumni(actor) and _has(actor, *STAFF_SCOPE_PERMISSIONS)
    )


_sees_everything = is_staff


# -- Leave Requests -----------------------------------------------------------
def leave_requests_for(actor) -> QuerySet[LeaveRequest]:
    """Base queryset for leave requests scoped by actor."""
    base = LeaveRequest.objects.all()

    user_id = _own_id(actor)

    if user_id is None:
        # No identity to scope by; return empty set.
        return base.none()

    # Default: show own requests unless staff sees all.
    if not _sees_everything(actor):
        return base.filter(user_id=user_id)

    # Staff / TPO / Director sees everything.
    return base.all()


def leave_request_by_id(request_id: int, actor) -> LeaveRequest | None:
    """Retrieve a specific request. Returns None if not found or unauthorized."""
    try:
        req = LeaveRequest.objects.get(id=request_id)
    except LeaveRequest.DoesNotExist:
        return None

    # Authorization check based on role.
    if _sees_everything(actor):
        return req

    # Check ownership or specific permission.
    if req.user_id == _own_id(actor):
        return req

    # Check if actor is a task assignee (limited read).
    try:
        WorkflowTask.objects.get(
            request_id_id=request_id,
            assigned_user_id=_own_id(actor),
        )
    except WorkflowTask.DoesNotExist:
        return None
    # Allow read for task assignees.
    return req


# -- Workflow Tasks -----------------------------------------------------------
def workflow_tasks_for(actor) -> QuerySet[WorkflowTask]:
    """Base queryset for workflow tasks scoped by actor."""
    base = WorkflowTask.objects.select_related(
        "request",
    )

    user_id = _own_id(actor)

    if user_id is None:
        return base.none()

    # Default: show own tasks unless staff sees all.
    if not _sees_everything(actor):
        return base.filter(assigned_user_id=user_id)

    # Staff / TPO / Director sees everything.
    return base.all()


def workflow_task_by_id(task_id: int, actor) -> WorkflowTask | None:
    """Retrieve a specific task. Returns None if not found or unauthorized."""
    try:
        task = WorkflowTask.objects.get(id=task_id)
    except WorkflowTask.DoesNotExist:
        return None

    # Authorization check based on role.
    if _sees_everything(actor):
        return task

    # Check ownership or specific permission.
    if task.assigned_user_id == _own_id(actor):
        return task

    return None


# -- Substitute Assignments ---------------------------------------------------
def substitute_assignments_for(actor) -> QuerySet[SubstituteAssignment]:
    """Base queryset for substitute assignments scoped by actor."""
    base = SubstituteAssignment.objects.select_related("request")

    user_id = _own_id(actor)

    if user_id is None:
        return base.none()

    # Default: show own assignments unless staff sees all.
    if not _sees_everything(actor):
        return base.filter(applicant_user_id=user_id)

    # Staff / TPO / Director sees everything.
    return base.all()


def substitute_assignment_by_id(assignment_id: int, actor) -> SubstituteAssignment | None:
    """Retrieve a specific assignment. Returns None if not found or unauthorized."""
    try:
        assign = SubstituteAssignment.objects.get(id=assignment_id)
    except SubstituteAssignment.DoesNotExist:
        return None

    # Authorization check based on role.
    if _sees_everything(actor):
        return assign

    # Check ownership or specific permission.
    if assign.applicant_user_id == _own_id(actor):
        return assign

    return None


# -- Helpers for Employee Context --------------------------------------------
def get_employee_for_request(request: LeaveRequest) -> EmployeeDTO | None:
    """Get employee details for a leave request using public contract."""
    try:
        user_ref = UserRef.objects.get(user_id=request.user_id)
        return EmployeeDTO.from_ref(user_ref)
    except UserRef.DoesNotExist:
        return None


def get_employees_for_unit(unit_designation: str) -> list[EmployeeDTO]:
    """Get employees belonging to a specific unit/designation.

    This is a public contract for cross-module data access without FKs.
    """
    # Placeholder implementation following blueprint pattern.
    # In production, this would query the directory module via contracts.
    return []


def get_eligible_substitutes(
    applicant_user_id: int,
    request: LeaveRequest,
) -> list[EmployeeDTO]:
    """Get eligible substitute employees for a leave request.

    Eligibility criteria:
    - Not the applicant.
    - No overlapping pending or approved leave during responsibility period.
    - Must be an employee (not retired/alumni).
    """
    # Placeholder implementation following blueprint pattern.
    # In production, this would query directory module via contracts and check balances.
    return []


# -- SLA Thresholds ----------------------------------------------------------
def get_sla_config(actor) -> dict:
    """Get current configured SLA thresholds for the actor.

    Uses current configured values only; no draft/publish/effective-version lifecycle.
    """
    # Placeholder implementation following blueprint pattern.
    return {
        "reminder_threshold_hours": 24,
        "escalation_threshold_hours": 48,
    }


def check_sla_threshold(task: WorkflowTask, actor) -> bool:
    """Check if a task has exceeded SLA thresholds.

    Returns True if the task is still pending and exceeds configured thresholds.
    """
    config = get_sla_config(actor)
    if task.due_date is None:
        return False
    due_hours = (task.due_date - task.created_at.date()).days * 24

    return (
        task.state in {"PENDING", "ASSIGNED"}
        and due_hours > config["reminder_threshold_hours"]
        and due_hours > config["escalation_threshold_hours"]
    )


# -- Unresolved Gaps ---------------------------------------------------------
# TODO: Import HR employment contract when available (e.g., from modules.hr)
# from modules.hr.models import Employment
# TODO: Import Academic Calendar contract when available (e.g., from modules.academic_calendar)
# from modules.academic_calendar.models import VacationPeriod
# TODO: Implement get_eligible_substitutes with actual overlap/balance checks.
# TODO: Implement get_employees_for_unit with actual directory queries."""
