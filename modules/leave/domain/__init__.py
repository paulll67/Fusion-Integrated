"""
Employee Leave Management (ELM) â Domain Package Exports.

This module defines the core domain aggregates, value objects, and state machines required for leave lifecycle management.
It remains independent from DRF and ORM internals; database interactions are handled via services using public contracts.
Identity references are integer user_id values.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Optional

# -- Enums and Constants (Derived from WF v1.6 and PS v1.4) --


class LeaveCategory(Enum):
    """Leave categories supported by ELM."""

    CL = "CL"  # Casual Leave
    RH = "RH"  # Restricted Holiday
    SCL = "SCL"  # Special Casual Leave
    EL = "EL"  # Earned Leave (Non-faculty)
    VL = "VL"  # Vacation Leave (Faculty)
    COL = "COL"  # Compensatory/Overtime Leave


class RequestStatus(Enum):
    """States for a LeaveRequest aggregate."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    AWAITING_SUBSTITUTE_RESPONSE = "AWAITING_SUBSTITUTE_RESPONSE"
    AWAITING_UNIT_HEAD_REVIEW = "AWAITING_UNIT_HEAD_REVIEW"
    AWAITING_HIERARCHY_APPROVAL = "AWAITING_HIERARCHY_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    CANCELLED = "CANCELLED"
    EXTENDED = "EXTENDED"
    RESUMPTION_REVIEW_PENDING = "RESUMPTION_REVIEW_PENDING"


class WorkflowTaskState(Enum):
    """States for a WorkflowTask aggregate."""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    ESCALATED = "ESCALATED"


class LeaveAccountTransactionType(Enum):
    """Types of entries in the LeaveLedger."""

    ALLOCATION = "ALLOCATION"
    CONSUMPTION = "CONSUMPTION"
    CARRY_FORWARD = "CARRY_FORWARD"
    EXTENSION_ADDITION = "EXTENSION_ADDITION"
    CANCELLATION_ADJUSTMENT = "CANCELLATION_ADJUSTMENT"
    RESUMPTION_ADJUSTMENT = "RESUMPTION_ADJUSTMENT"
    OFFLINE_RECORD_SYNC = "OFFLINE_RECORD_SYNC"
    YEAR_END_CONVERSION = "YEAR_END_CONVERSION"


class LeaveAccountBalance(Enum):
    """Available balance categories."""

    CL_BALANCE = "CL_BALANCE"
    RH_BALANCE = "RH_BALANCE"
    SCL_BALANCE = "SCL_BALANCE"
    EL_BALANCE = "EL_BALANCE"
    VL_BALANCE = "VL_BALANCE"
    COL_BALANCE = "COL_BALANCE"


class LeaveAccount(Enum):
    """Aggregate representing an employee's leave balance."""

    CL = LeaveAccountBalance.CL_BALANCE
    RH = LeaveAccountBalance.RH_BALANCE
    SCL = LeaveAccountBalance.SCL_BALANCE
    EL = LeaveAccountBalance.EL_BALANCE
    VL = LeaveAccountBalance.VL_BALANCE
    COL = LeaveAccountBalance.COL_BALANCE


class RequestActionType(Enum):
    """Types of actions recorded in the history."""

    SUBMIT = "SUBMIT"
    WITHDRAW = "WITHDRAW"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CANCEL = "CANCEL"
    EXTEND = "EXTEND"
    RESUME_REVIEW = "RESUME_REVIEW"
    OFFLINE_SYNC = "OFFLINE_SYNC"
    YEAR_END_PROCESS = "YEAR_END_PROCESS"


class SubstituteResponse(Enum):
    """Substitute assignment responses."""

    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"


# -- Value Objects --


class LeavePeriod:
    """Represents the requested leave interval."""

    def __init__(self, start_date: date, end_date: date) -> None:
        self.start_date: date = start_date
        self.end_date: date = end_date

    @property
    def duration_days(self) -> int:
        """Calculate total days including weekends/holidays per counting rules."""
        # Note: Implementation of specific counting rules (CL vs EL/VL) is in services.
        return (self.end_date - self.start_date).days + 1


class LeaveRequest:
    """Aggregate representing a single leave application lifecycle."""

    def __init__(
        self,
        id: int,
        employee_user_id: int,
        category: LeaveCategory,
        period: LeavePeriod,
        purpose: str | None = None,
        station_leave_details: dict | None = None,
        status: RequestStatus = RequestStatus.DRAFT,
        submitted_at: date | None = None,
        substitute_user_id: int | None = None,
    ) -> None:
        self.id: int = id
        self.employee_user_id: int = employee_user_id
        self.category: LeaveCategory = category
        self.period: LeavePeriod = period
        self.purpose: str | None = purpose
        self.station_leave_details: dict | None = station_leave_details
        self.status: RequestStatus = status
        self.submitted_at: date | None = submitted_at
        self.substitute_user_id: int | None = substitute_user_id
        # Internal state tracking for history and actions
        self._actions: list[dict[str, Any]] = []

    def submit(self) -> None:
        """Transition to SUBMITTED state."""
        if self.status == RequestStatus.DRAFT:
            self.status = RequestStatus.SUBMITTED
            self.submitted_at = date.today()
            self._actions.append(
                {
                    "type": RequestActionType.SUBMIT.value,
                    "timestamp": self.submitted_at.isoformat(),
                }
            )

    def withdraw(self) -> None:
        """Transition to WITHDRAWN state. Must be called before final approval."""
        if self.status in [
            RequestStatus.DRAFT,
            RequestStatus.SUBMITTED,
            RequestStatus.AWAITING_UNIT_HEAD_REVIEW,
        ]:
            self.status = RequestStatus.WITHDRAWN
            self._actions.append(
                {
                    "type": RequestActionType.WITHDRAW.value,
                    "timestamp": date.today().isoformat(),
                }
            )

    def cancel(self) -> None:
        """Transition to CANCELLED state. Must be called after approval but before start."""
        if self.status == RequestStatus.APPROVED:
            self.status = RequestStatus.CANCELLED
            # Balance adjustment logic handled in service layer
            self._actions.append(
                {
                    "type": RequestActionType.CANCEL.value,
                    "timestamp": date.today().isoformat(),
                }
            )

    def extend(self, new_end_date: date) -> None:
        """Transition to EXTENDED state for ongoing EL/COL/VL."""
        if self.status == RequestStatus.APPROVED:
            # Validation of overlap and balance in service layer
            self.period.end_date = new_end_date
            self.status = RequestStatus.EXTENDED
            self._actions.append(
                {
                    "type": RequestActionType.EXTEND.value,
                    "timestamp": date.today().isoformat(),
                }
            )

    def resumption_review(self, actual_return_date: date) -> None:
        """Transition to RESUMPTION_REVIEW_PENDING for early/late return."""
        if self.status == RequestStatus.APPROVED:
            self.period.end_date = actual_return_date
            self.status = RequestStatus.RESUMPTION_REVIEW_PENDING
            self._actions.append(
                {
                    "type": RequestActionType.RESUME_REVIEW.value,
                    "timestamp": date.today().isoformat(),
                }
            )

    def add_action(self, action_type: RequestActionType, reason: str) -> None:
        """Append an action to the history."""
        self._actions.append(
            {
                "type": action_type.value,
                "reason": reason,
                "timestamp": date.today().isoformat(),
            }
        )


class LeaveAccount:
    """Aggregate representing an employee's leave balance."""

    def __init__(self, employee_user_id: int) -> None:
        self.employee_user_id: int = employee_user_id
        self._balances: dict[LeaveCategory, float] = {
            LeaveCategory.CL: 0.0,
            LeaveCategory.RH: 0.0,
            LeaveCategory.SCL: 0.0,
            LeaveCategory.EL: 0.0,
            LeaveCategory.VL: 0.0,
            LeaveCategory.COL: 0.0,
        }

    def allocate(self, category: LeaveCategory, days: float) -> None:
        """Add days to the balance."""
        self._balances[category] += days

    def consume(self, category: LeaveCategory, days: float) -> bool:
        """Check and deduct days from the balance. Returns True if successful."""
        if self._balances[category] >= days:
            self._balances[category] -= days
            return True
        return False

    def get_balance(self, category: LeaveCategory) -> float:
        """Retrieve current balance for a category."""
        return self._balances.get(category, 0.0)

    def process_year_end(self) -> None:
        """Apply year-end conversion rules (VL to EL)."""
        # Rule: Unused VL converts to EL at 2 VL : 1 EL ratio
        vl_balance = self._balances.get(LeaveCategory.VL, 0.0)
        el_credit = vl_balance * 2.0
        self._balances[LeaveCategory.EL] += el_credit
        # Unused VL is effectively zeroed out (not carried forward as VL)
        self._balances[LeaveCategory.VL] = 0.0


class LeaveLedgerEntry:
    """Immutable record of a balance transaction."""

    def __init__(
        self,
        id: int,
        employee_user_id: int,
        category: LeaveCategory,
        transaction_type: LeaveAccountTransactionType,
        amount: float,
        reference_request_id: int | None = None,
    ) -> None:
        self.id: int = id
        self.employee_user_id: int = employee_user_id
        self.category: LeaveCategory = category
        self.transaction_type: LeaveAccountTransactionType = transaction_type
        self.amount: float = amount
        self.reference_request_id: int | None = reference_request_id


class WorkflowTask:
    """Aggregate representing a task in the leave approval workflow."""

    def __init__(
        self,
        id: int,
        request_id: int,
        task_kind: str,
        assigned_user_id: int | None = None,
        state: WorkflowTaskState = WorkflowTaskState.PENDING,
    ) -> None:
        self.id: int = id
        self.request_id: int = request_id
        self.task_kind: str = task_kind
        self.assigned_user_id: int | None = assigned_user_id
        self.state: WorkflowTaskState = state
        self.due_date: date | None = None
        self.reminder_sent: bool = False

    def assign(self, user_id: int) -> None:
        """Assign the task to a user."""
        if self.state == WorkflowTaskState.PENDING:
            self.state = WorkflowTaskState.ASSIGNED
            self.assigned_user_id = user_id

    def complete(self) -> None:
        """Mark the task as completed."""
        if self.state in [WorkflowTaskState.ASSIGNED, WorkflowTaskState.PENDING]:
            self.state = WorkflowTaskState.COMPLETED

    def escalate(self) -> None:
        """Escalate the task due to SLA threshold."""
        if self.state == WorkflowTaskState.PENDING:
            self.state = WorkflowTaskState.ESCALATED


class SubstituteAssignment:
    """Aggregate representing a substitute consent assignment."""

    def __init__(
        self,
        request_id: int,
        applicant_user_id: int,
        substitute_user_id: int,
        response: SubstituteResponse,
        responsibility_interval: LeavePeriod,
    ) -> None:
        self.request_id: int = request_id
        self.applicant_user_id: int = applicant_user_id
        self.substitute_user_id: int = substitute_user_id
        self.response: SubstituteResponse = response
        self.responsibility_interval: LeavePeriod = responsibility_interval


class HolidayRHCalendar:
    """Aggregate representing the published holiday/RH calendar."""

    def __init__(self, id: int, metadata: dict[str, Any], dates: list[date]) -> None:
        self.id: int = id
        self.metadata: dict[str, Any] = metadata
        self.dates: list[date] = dates
        self.is_published: bool = True


class SLAConfig:
    """Configuration for SLA thresholds and escalation."""

    def __init__(self, reminder_threshold_hours: int, escalation_threshold_hours: int) -> None:
        self.reminder_threshold_hours: int = reminder_threshold_hours
        self.escalation_threshold_hours: int = escalation_threshold_hours


class LeavePolicyConfig:
    """Current configured leave policy parameters (no lifecycle)."""

    def __init__(self) -> None:
        # Default values as per PS v1.4 unless overridden by config service
        self.cl_entitlement = 8.0
        self.rh_entitlement = 2.0
        self.scl_entitlement = 15.0
        self.el_entitlement = 30.0
        self.vl_entitlement = 60.0
        self.col_entitlement = 20.0
        # Carry forward rules are handled in domain logic or services


class HierarchyConfig:
    """Configuration for organizational routing."""

    def __init__(self) -> None:
        # Default routing structure
        self.unit_head_role = "Unit Head"
        self.establishment_step_enabled: bool = False
        self.director_self_sanction_enabled: bool = True


class ResumptionRecord:
    """Aggregate for resumption review outcomes."""

    def __init__(
        self,
        request_id: int,
        actual_return_date: date,
        outcome: str,  # 'NORMAL', 'EARLY', 'LATE'
        reviewed_by_user_id: int | None = None,
    ) -> None:
        self.request_id: int = request_id
        self.actual_return_date: date = actual_return_date
        self.outcome: str = outcome
        self.reviewed_by_user_id: int | None = reviewed_by_user_id


class OfflineSanctionRecord:
    """Aggregate for already-sanctioned offline leave synchronization."""

    def __init__(
        self,
        employee_user_id: int,
        category: LeaveCategory,
        interval: LeavePeriod,
        source_leave_account_transaction_id: int | None = None,
    ) -> None:
        self.employee_user_id: int = employee_user_id
        self.category: LeaveCategory = category
        self.interval: LeavePeriod = interval
        self.source_leave_account_transaction_id: int | None = source_leave_account_transaction_id


"}"
