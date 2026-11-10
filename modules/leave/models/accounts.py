"""
Leave Account and Ledger Models (ELM) â Append-only structures.

This module defines aggregates for leave entitlements, consumption, carry-forward,
and adjustments. Balances are derived from explicit ledger entries to avoid
editable balance-only accounting patterns. All identity references use integer user_id.
"""

from datetime import date
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.db.mixins import TimeStampedModel

# -----------------------------------------------------------------------------
# Leave Account Aggregates
# -----------------------------------------------------------------------------


class LeaveAccount(TimeStampedModel):
    """Aggregate representing an employee's leave balance for a specific category.

    Balances are immutable; changes occur via LedgerEntry transactions.
    """

    user_id = models.IntegerField(db_index=True)  # IAM user ID
    category = models.CharField(max_length=20, db_index=True)  # CL, RH, SCL, EL, COL, VL
    year = models.PositiveSmallIntegerField()  # Fiscal year (e.g., 2026)

    balance = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(0)]
    )
    is_faculty = models.BooleanField(default=False)  # Determines VL applicability

    class Meta:
        db_table = "leave_account"
        unique_together = ["user_id", "category", "year"]
        verbose_name = "leave account"
        ordering = ["-year", "-balance"]

    def __str__(self) -> str:
        return f"{self.user_id} ({self.category}) {self.year}: {self.balance}"


# -----------------------------------------------------------------------------
# Leave Ledger Entries (Append-only History)
# -----------------------------------------------------------------------------


class LeaveLedgerEntry(TimeStampedModel):
    """Immutable record of a balance change.

    This table serves as the source of truth for balance calculations.
    It records the type, amount, reference (request ID), and reason.
    """

    user_id = models.IntegerField(db_index=True)  # IAM user ID
    category = models.CharField(max_length=20, db_index=True)
    year = models.PositiveSmallIntegerField()

    entry_type = models.CharField(
        max_length=50, db_index=True
    )  # e.g., 'APPROVAL', 'CARRY_FORWARD', 'YEAR_END_LAPSE'
    amount = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    reference_request_id: int | None = models.IntegerField(
        null=True, blank=True
    )  # Linked LeaveRequest ID
    reason = models.TextField(blank=True)  # e.g., 'Approved', 'Unused VL converted'

    class Meta:
        db_table = "leave_ledger_entry"
        unique_together = [
            "user_id",
            "category",
            "year",
        ]  # One entry per category/year per user (conceptually, though multiple types might exist)
        verbose_name = "leave ledger entry"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user_id} ({self.category}) {self.year}: {self.entry_type} - {self.amount}"


# -----------------------------------------------------------------------------
# Leave Request (Lifecycle & State)
# -----------------------------------------------------------------------------


class LeaveRequest(TimeStampedModel):
    """Core leave application aggregate.

    Once submitted, the request cannot be modified in place. Changes require
    withdrawal or cancellation workflows.
    """

    user_id = models.IntegerField(db_index=True)  # IAM user ID (Applicant)
    category = models.CharField(max_length=20, db_index=True)  # CL, RH, SCL, EL, COL, VL

    start_date = models.DateField()
    end_date = models.DateField()
    purpose = models.TextField(blank=True)
    station_leave_details: dict | None = models.JSONField(
        null=True, blank=True
    )  # Only for Station Leave

    status = models.CharField(
        max_length=50, db_index=True, default="DRAFT"
    )  # DRAFT, SUBMITTED, PENDING_SUBSTITUTE, PENDING_REVIEW, APPROVED, REJECTED, WITHDRAWN, CANCELLED, EXTENDED, RESUMED

    has_substitute = models.BooleanField(default=False)
    substitute_user_id: int | None = models.IntegerField(
        null=True, blank=True
    )  # IAM user ID of substitute

    is_cancelled = models.BooleanField(default=False)  # Flag for pre-start cancellation
    cancelled_at: date | None = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "leave_request"
        verbose_name = "leave request"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user_id} ({self.category}) {self.start_date}-{self.end_date}: {self.status}"


# -----------------------------------------------------------------------------
# Workflow Task (Actionable Assignments)
# -----------------------------------------------------------------------------


class WorkflowTask(TimeStampedModel):
    """Tracks actionable assignments within a leave request lifecycle.

    Tasks are created when a request moves to a state requiring human action.
    Completed tasks must not be reprocessed.
    """

    request_id = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name="tasks")
    task_kind = models.CharField(max_length=50)  # e.g., 'UNIT_HEAD_REVIEW', 'SUBSTITUTE_RESPONSE'
    assigned_user_id: int | None = models.IntegerField(null=True, blank=True)  # IAM user ID (Actor)
    state = models.CharField(
        max_length=50, db_index=True, default="PENDING"
    )  # PENDING, ASSIGNED, COMPLETED, ESCALATED
    due_date = models.DateField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    escalation_triggered = models.BooleanField(default=False)

    class Meta:
        db_table = "workflow_task"
        verbose_name = "leave workflow task"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Task {self.request_id} ({self.task_kind}) - {self.state}"


# -----------------------------------------------------------------------------
# Request Action History (Audit Trail)
# -----------------------------------------------------------------------------


class RequestAction(TimeStampedModel):
    """Append-only history of actions taken on a leave request.

    This table records who did what and the outcome, independent of state changes.
    """

    request_id = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name="actions")
    actor_user_id: int | None = models.IntegerField(null=True, blank=True)  # IAM user ID (Actor)
    action_type = models.CharField(
        max_length=50
    )  # e.g., 'SUBMITTED', 'APPROVED', 'REJECTED', 'WITHDRAWN'
    outcome = models.TextField(blank=True)  # e.g., 'Approved for 5 days'
    reason = models.TextField(blank=True)  # Evidence or justification

    class Meta:
        db_table = "request_action"
        verbose_name = "leave request action"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Action {self.request_id} by {self.actor_user_id}: {self.action_type}"


# -----------------------------------------------------------------------------
# Substitute Assignment (Consent Gate)
# -----------------------------------------------------------------------------


class SubstituteAssignment(TimeStampedModel):
    """Records the nomination and response of a substitute employee.

    Required for certain leave categories or when responsibility coverage is mandated.
    """

    request_id = models.ForeignKey(
        LeaveRequest, on_delete=models.CASCADE, related_name="substitute_assignments"
    )
    applicant_user_id: int | None = models.IntegerField(
        null=True, blank=True
    )  # IAM user ID (Applicant)
    substitute_user_id: int | None = models.IntegerField(
        null=True, blank=True
    )  # IAM user ID (Substitute)
    response = models.CharField(
        max_length=20, db_index=True, default="DECLINED"
    )  # ACCEPTED, DECLINED
    responsibility_interval_start = models.DateField()
    responsibility_interval_end = models.DateField()

    class Meta:
        db_table = "substitute_assignment"
        verbose_name = "leave substitute assignment"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Sub {self.request_id} by {self.substitute_user_id}: {self.response}"


# -----------------------------------------------------------------------------
# Resumption Record (EL/COL/VL Specific)
# -----------------------------------------------------------------------------


class ResumptionRecord(TimeStampedModel):
    """Tracks actual resumption of approved leave.

    Used for Early, Normal, and Late return scenarios to synchronize balances.
    """

    request_id = models.ForeignKey(
        LeaveRequest, on_delete=models.CASCADE, related_name="resumptions"
    )
    actual_start_date = models.DateField()  # When employee actually returned
    review_status = models.CharField(
        max_length=50, default="PENDING"
    )  # PENDING, REVIEWED, APPROVED
    review_outcome = models.TextField(blank=True)  # e.g., 'Late return approved'

    class Meta:
        db_table = "resumption_record"
        verbose_name = "leave resumption record"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Resum {self.request_id} on {self.actual_start_date}: {self.review_status}"


# -----------------------------------------------------------------------------
# Offline Sanction Record (Record Integrity)
# -----------------------------------------------------------------------------


class OfflineSanctionRecord(TimeStampedModel):
    """Synchronizes already-sanctioned offline/paper leave.

    Does not issue a second sanction; records the evidence and consistency outcome.
    """

    employee_user_id: int | None = models.IntegerField(null=True, blank=True)  # IAM user ID
    category = models.CharField(max_length=20)
    interval_start = models.DateField()
    interval_end = models.DateField()
    sanction_reference = models.TextField(blank=True)  # Paper file reference
    consistency_outcome = models.CharField(
        max_length=50, default="CONSISTENT"
    )  # CONSISTENT, INCONSISTENT
    source_transaction_id: int | None = models.IntegerField(
        null=True, blank=True
    )  # Linked LedgerEntry ID

    class Meta:
        db_table = "offline_sanction_record"
        verbose_name = "leave offline sanction record"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Offline {self.category} {self.interval_start}-{self.interval_end}: {self.consistency_outcome}"


# -----------------------------------------------------------------------------
# Configuration Models (Current Values Only)
# -----------------------------------------------------------------------------


class LeavePolicyConfig(TimeStampedModel):
    """Current leave entitlements and counting parameters.

    No draft/publish/effective-version lifecycle; uses current configured values only.
    """

    category = models.CharField(max_length=20, db_index=True)  # CL, RH, SCL, EL, COL, VL
    annual_entitlement = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )
    counting_rule = models.CharField(
        max_length=50, default="CONTINUOUS"
    )  # CONTINUOUS (EL/COL/VL), STANDARD (CL/RH/SCL)
    carry_forward_allowed = models.BooleanField(
        default=False
    )  # True for EL/COL, False for CL/RH/SCL/VL

    class Meta:
        db_table = "leave_policy_config"
        unique_together = ["category"]
        verbose_name = "leave policy config"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.category}: {self.annual_entitlement} days ({self.carry_forward_allowed})"


class HierarchyConfig(TimeStampedModel):
    """Current routing hierarchy and optional Establishment step.

    Resolution belongs in the domain/service layer; this stores current facts.
    """

    unit_head_role = models.CharField(max_length=50, blank=True)  # e.g., 'UNIT_HEAD'
    establishment_step_required = models.BooleanField(default=False)  # Optional routing step
    establishment_role = models.CharField(max_length=50, blank=True)  # e.g., 'ESTABLISHMENT_HEAD'
    director_self_sanction = models.BooleanField(default=False)  # Exception rule

    class Meta:
        db_table = "hierarchy_config"
        verbose_name = "leave hierarchy config"
        ordering = ["-created_at"]


class SLAConfig(TimeStampedModel):
    """SLA thresholds and escalation behavior.

    Used by event-triggered processing; current values apply.
    """

    reminder_threshold_hours = models.PositiveIntegerField(default=48)  # Hours before due date
    escalation_threshold_hours = models.PositiveIntegerField(default=24)  # Hours before due date
    escalation_action = models.CharField(
        max_length=50, default="ROUTE_TO_SUPERIOR"
    )  # e.g., 'ROUTE_TO_SUPERIOR'

    class Meta:
        db_table = "sla_config"
        verbose_name = "leave SLA config"
        ordering = ["-created_at"]


class HolidayRHCalendar(TimeStampedModel):
    """Currently effective published holiday/RH calendar.

    Only the currently effective published calendar is used for validation.
    """

    name = models.CharField(max_length=100)  # e.g., '2026-Holidays'
    publication_date = models.DateField()
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)  # Null means perpetual
    is_published = models.BooleanField(default=False)

    # Dates and markers
    restricted_holidays: list[date] = models.JSONField(default=list)  # RH dates
    holiday_markers: list[dict] = models.JSONField(default=list)  # {date, name, type}

    class Meta:
        db_table = "holiday_rh_calendar"
        verbose_name = "leave holiday calendar"
        ordering = ["-publication_date"]


class VacationPeriodConfig(TimeStampedModel):
    """Vacation period applicability for VL (Faculty).

    Derived from external Academic Calendar service; stored here for local access.
    """

    name = models.CharField(max_length=100)  # e.g., 'Summer Vacation 2026'
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)  # Only active periods apply

    class Meta:
        db_table = "vacation_period_config"
        verbose_name = "leave vacation period"
        ordering = ["-start_date"]
