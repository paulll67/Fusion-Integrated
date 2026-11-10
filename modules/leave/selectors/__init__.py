"""
Leave Management (ELM) — Selectors Package Exports.

The selectors module provides public interfaces to retrieve leave-related aggregates,
state transitions, and configuration data without cross-module database joins or direct table reads.
All identity references are integer user_id values. Cross-module data access must use these public contracts.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fusion_auth.client import IamUnavailable, get_client
from modules.directory.models import UserRef
from modules.directory.services.sync import ensure_users_cached

# TODO: Import HR employment contract when available (e.g., from modules.hr)
# from modules.hr.models import Employment
# TODO: Import Academic Calendar contract when available (e.g., from modules.academic_calendar)
# from modules.academic_calendar.models import VacationPeriod


@dataclass(frozen=True)
class EmployeeDTO:
    """Employee projection for leave eligibility and balance checks."""

    user_id: int
    username: str
    display_name: str
    kind: str  # 'faculty' or 'staff'
    email: str = ""
    department: str = ""
    designation: str = ""
    batch_year: int | None = None

    @classmethod
    def from_ref(cls, r: UserRef) -> EmployeeDTO:
        return cls(
            user_id=r.user_id,
            username=r.username,
            display_name=r.display_name,
            kind=r.kind,
            email=r.email,
            department=r.department,
            designation=r.designation or "",
            batch_year=r.batch_year,
        )


@dataclass(frozen=True)
class LeaveBalanceDTO:
    """Leave balance projection for a specific employee and category.
    Includes current available days and carry-forward status.
    """

    user_id: int
    category: str  # 'CL', 'RH', 'SCL', 'EL', 'VL', 'COL'
    available_days: float
    carries_forward: bool = False
    year_end_balance: float | None = None


@dataclass(frozen=True)
class WorkflowTaskDTO:
    """Workflow task projection for actionable assignments.
    Tracks current state and due information.
    """

    task_id: int
    request_id: int
    kind: str  # 'review', 'sanction', 'substitute_response'
    assigned_user_id: int | None = None
    role: str | None = None
    state: str = "pending"  # 'pending', 'assigned', 'completed'
    due_date: str | None = None
    reminder_sent: bool = False


@dataclass(frozen=True)
class LeaveRequestDTO:
    """Leave request projection for status and lifecycle inspection.
    Excludes internal state machine details; exposes public fields only.
    """

    id: int
    employee_user_id: int
    category: str  # 'CL', 'RH', 'SCL', 'EL', 'COL', 'VL'
    start_date: str
    end_date: str
    status: str  # 'draft', 'submitted', 'approved', 'rejected', 'cancelled'
    has_substitute: bool = False
    substitute_user_id: int | None = None
    submitted_at: str | None = None


@dataclass(frozen=True)
class LeavePolicyDTO:
    """Current leave policy configuration values.
    No draft/publish/effective-version lifecycle; uses current configured values only.
    """

    category: str  # 'CL', 'RH', 'SCL', 'EL', 'VL', 'COL'
    annual_entitlement: float
    carries_forward: bool = False
    counting_rule: str = "calendar"  # 'continuous', 'calendar'


@dataclass(frozen=True)
class HierarchyConfigDTO:
    """Current hierarchy routing configuration.
    Defines the path for sanctioning based on role/unit/category.
    """

    unit_head_role: str | None = None
    establishment_step_required: bool = False
    final_sanctioning_roles: Sequence[str] = ()


@dataclass(frozen=True)
class HolidayRHCalendarDTO:
    """Currently effective published holiday/RH calendar data.
    Used for date and RH marker validation.
    """

    year: int
    holidays: Sequence[str]  # ISO date strings
    restricted_holidays: Sequence[str]
    is_published: bool = True


@dataclass(frozen=True)
class SLAConfigDTO:
    """Current SLA threshold configuration.
    Used by event-triggered processing; current values apply.
    """

    reminder_threshold_hours: int = 24
    escalation_threshold_hours: int = 72
    escalation_action: str = "notify_and_route"


# TODO: Implement concrete selector functions here when domain models are fully wired.
# These placeholders indicate the public API surface for external modules.


def get_employee(user_id: int) -> EmployeeDTO | None:
    """Retrieve employee details by user ID.
    Returns None if user not found or IAM unavailable.
    """


def get_leave_balance(user_id: int, category: str) -> LeaveBalanceDTO | None:
    """Retrieve leave balance for a specific employee and category.
    Handles carry-forward logic and year-end conversion rules.
    """


def get_pending_tasks(request_id: int) -> Sequence[WorkflowTaskDTO]:
    """Retrieve pending workflow tasks for a specific request.
    Returns empty sequence if no tasks or request not found.
    """


def get_leave_request(request_id: int) -> LeaveRequestDTO | None:
    """Retrieve leave request details by ID.
    Returns None if request not found.
    """


def get_current_policy(category: str) -> LeavePolicyDTO | None:
    """Retrieve current leave policy configuration for a category.
    Uses current configured values without version lifecycle.
    """


def get_hierarchy_config() -> HierarchyConfigDTO:
    """Retrieve current hierarchy routing configuration."""


def get_effective_calendar(year: int) -> HolidayRHCalendarDTO | None:
    """Retrieve the currently effective published holiday/RH calendar for a year.
    Returns None if no valid calendar exists.
    """


def get_sla_config() -> SLAConfigDTO:
    """Retrieve current SLA threshold configuration."""


# NOTE: Unresolved implementation gaps exist in the domain service layer for
# concrete data retrieval (e.g., LeaveAccount, WorkflowTask tables).
# These selectors are defined here to maintain public contracts; actual logic
# must be implemented in services/leave/*.py once database wiring is complete.
