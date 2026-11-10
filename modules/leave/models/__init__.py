"""
Employee Leave Management (ELM) — Models.

This module defines the domain aggregates and entities required for leave processing,
balance management, workflow tracking, and policy configuration.

All identity references are integer user_id values. Cross-module data access must use
public contracts defined in modules.leave.contracts, not direct table reads or foreign keys.
"""
from __future__ import annotations

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from django.db import models
    from modules.directory.models import UserRef


class LeaveRequest(models.Model):
    """
    Core leave application aggregate.
    
    Responsibilities:
    - Store request metadata (category, period, purpose).
    - Track lifecycle state via WorkflowTask integration.
    - Enforce immutability after submission.
    """
    class Meta:
        app_label = 'leave'
        ordering = ['-created_at']

    # Identity
    employee_user_id: int
    
    # Category (CL, RH, SCL, EL, COL, VL)
    category: str
    
    # Period
    start_date: date
    end_date: date
    
    # Details
    purpose: Optional[str] = None
    station_leave_details: Optional[str] = None  # JSON or text for Station Leave specifics
    
    # Lifecycle
    status: str = 'DRAFT'
    submitted_at: Optional[date] = None
    created_at: date = models.Field(default=date.today)
    updated_at: date = models.Field(default=date.today)
    
    # Links (via contracts, not FKs)
    original_request_id: Optional[int] = None  # For resumption or replacement scenarios
    
    class StatusChoices(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBSTITUATE_PENDING = 'SUBSTITUATE_PENDING', 'Substitute Pending'
        UNIT_HEAD_REVIEW = 'UNIT_HEAD_REVIEW', 'Unit Head Review'
        HIERARCHY_ROUTING = 'HIERARCHY_ROUTING', 'Hierarchy Routing'
        FINAL_APPROVED = 'FINAL_APPROVED', 'Final Approved'
        FINAL_REJECTED = 'FINAL_REJECTED', 'Final Rejected'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXTENSION_PENDING = 'EXTENSION_PENDING', 'Extension Pending'
        RESUMPTION_PENDING = 'RESUMPTION_PENDING', 'Resumption Pending'

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_date <= end_date),
                name='unique_leave_period'
            )
        ]


class WorkflowTask(models.Model):
    """
    Tracks actionable assignments and current task state.
    
    Responsibilities:
    - Link to a LeaveRequest or ResumptionRecord.
    - Store assignment details (assignee, due date, escalation).
    - Enforce idempotency for completed tasks.
    """
    class Meta:
        app_label = 'leave'
        ordering = ['-created_at']

    # Reference
    request_id: int
    resumption_record_id: Optional[int] = None
    
    # Task Details
    task_kind: str  # e.g., 'SUBSTITUTE_RESPONSE', 'UNIT_HEAD_REVIEW', 'FINAL_DECISION'
    assignee_user_id: int
    role_context: str  # e.g., 'UNIT_HEAD', 'DIRECTOR'
    state: str = 'PENDING'
    
    assigned_at: Optional[date] = None
    due_date: Optional[date] = None
    reminder_sent_at: Optional[date] = None
    escalated_at: Optional[date] = None
    completed_at: Optional[date] = None
    
    class StateChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        COMPLETED = 'COMPLETED', 'Completed'
        ESCALATED = 'ESCALATED', 'Escalated'


class RequestAction(models.Model):
    """
    Append-oriented action history for user-visible status and operations.
    
    Responsibilities:
    - Record every state transition or modification.
    - Store actor identity (user_id) and outcome.
    """
    class Meta:
        app_label = 'leave'
        ordering = ['-timestamp']

    # Reference
    request_id: int
    
    # Action Details
    actor_user_id: int
    action_type: str  # e.g., 'SUBMITTED', 'APPROVED', 'REJECTED', 'WITHDRAWN'
    outcome: Optional[str] = None  # Human-readable result
    reason: Optional[str] = None
    evidence_reference: Optional[str] = None
    
    timestamp: date = models.Field(default=date.today)


class LeaveAccount(models.Model):
    """
    Employee leave balance aggregate.
    
    Responsibilities:
    - Maintain current balance per category.
    - Track transactions (entries) for audit and calculation.
    - Support concurrency-sensitive updates via explicit ledger entries.
    """
    class Meta:
        app_label = 'leave'
        ordering = ['-created_at']

    # Identity
    employee_user_id: int
    
    # Category (CL, RH, EL, COL, VL)
    category: str
    
    # Balance
    balance: Decimal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Metadata
    year_end_source_id: Optional[int] = None  # Link to YearEndProcessingRecord if applicable
    last_updated_at: date = models.Field(default=date.today)


class LeaveLedgerEntry(models.Model):
    """
    Immutable transaction log for LeaveAccount.
    
    Responsibilities:
    - Record every balance change (approval, extension, cancellation).
    - Enable reconciliation and audit trails.
    """
    class Meta:
        app_label = 'leave'
        ordering = ['-timestamp']

    # Reference
    account_id: int
    
    # Transaction Details
    transaction_type: str  # e.g., 'APPROVAL', 'EXTENSION', 'CANCELLATION', 'YEAR_END_CONVERSION'
    amount: Decimal
    reference_request_id: Optional[int] = None
    description: str
    timestamp: date = models.Field(default=date.today)


class SubstituteAssignment(models.Model):
    """
    Tracks substitute consent and replacement logic.
    
    Responsibilities:
    - Link request to applicant and substitute.
    - Enforce eligibility (substitute != applicant, no overlapping leave).
    """
    class Meta:
        app_label = 'leave'
        ordering = ['-created_at']

    # Reference
    request_id: int
    
    # Parties
    applicant_user_id: int
    substitute_user_id: int
    
    # Response
    response: str  # 'ACCEPTED', 'DECLINED'
    responsibility_interval_start: date
    responsibility_interval_end: date
    
    created_at: date = models.Field(default=date.today)
    updated_at: date = models.Field(default=date.today)


class LeavePolicyConfig(models.Model):
    """
    Current configured leave entitlements and parameters.
    
    Responsibilities:
    - Store active policy values (no draft/publish lifecycle).
    - Provide read-only access for validation services.
    """
    class Meta:
        app_label = 'leave'
        ordering = []

    # Category specific entitlements
    cl_entitlement: int = models.IntegerField(default=8)
    rh_entitlement: int = models.IntegerField(default=2)
    scl_entitlement: int = models.IntegerField(default=15)
    el_entitlement: int = models.IntegerField(default=30)
    col_entitlement: int = models.IntegerField(default=20)
    
    # Faculty specific
    vl_entitlement: int = models.IntegerField(default=60)  # Days per period
    
    # General rules
    cl_half_day_consumption: bool = models.BooleanField(default=True)
    unused_el_carry_forward: bool = models.BooleanField(default=True)
    unused_col_carry_forward: bool = models.BooleanField(default=True)
    unused_vl_conversion_rate: int = models.IntegerField(default=2)  # 2 VL : 1 EL
    
    updated_at: date = models.Field(default=date.today)


class HierarchyConfig(models.Model):
    """
    Organizational unit and routing configuration.
    
    Responsibilities:
    - Define Unit Head, Establishment step, and Sanctioning Authority.
    - Store current routing facts (no versioning).
    """
    class Meta:
        app_label = 'leave'
        ordering = []

    # Routing Structure
    unit_head_role: str  # e.g., 'UNIT_HEAD', 'DEPUTY_REGISTRAR'
    establishment_step_required: bool = models.BooleanField(default=False)
    establishment_role: Optional[str] = None  # e.g., 'ESTABLISHMENT_HEAD'
    
    # Sanctioning Authority
    final_sanctioning_authority: str  # e.g., 'DIRECTOR', 'REGISTRAR'
    director_self_sanction_allowed: bool = models.BooleanField(default=False)
    
    updated_at: date = models.Field(default=date.today)


class HolidayRHCalendar(models.Model):
    """
    Published holiday and Restricted Holiday calendar.
    
    Responsibilities:
    - Store metadata and dates.
    - Enforce publication state (only published is effective).
    """
    class Meta:
        app_label = 'leave'
        ordering = ['date']

    # Metadata
    title: str
    year: int
    
    # State
    is_published: bool = models.BooleanField(default=False)
    published_at: Optional[date] = None
    
    # Dates
    date: date = models.DateField(unique=True)
    holiday_marker: str  # 'HOLIDAY', 'RESTRICTED_HOLIDAY'
    description: Optional[str] = None


class ResumptionRecord(models.Model):
    """
    Tracks actual resumption of approved leave.
    
    Responsibilities:
    - Link to original approved request.
    - Record actual start/end dates.
    - Support review and balance synchronization.
    """
    class Meta:
        app_label = 'leave'
        ordering = ['-created_at']

    # Reference
    request_id: int
    
    # Actual Dates
    actual_start_date: date
    actual_end_date: date
    
    # Details
    reason_for_early_late_return: Optional[str] = None
    review_status: str = 'PENDING'
    reviewed_outcome: Optional[str] = None  # 'NORMAL', 'EARLY_SYNC', 'LATE_SYNC'
    
    created_at: date = models.Field(default=date.today)
    updated_at: date = models.Field(default=date.today)


class OfflineSanctionRecord(models.Model):
    """
    Records already-sanctioned offline/paper leave.
    
    Responsibilities:
    - Synchronize authorized offline leave with the system.
    - Prevent duplicate sanctioning.
    """
    class Meta:
        app_label = 'leave'
        ordering = ['-created_at']

    # Reference
    employee_user_id: int
    
    # Leave Details
    category: str
    start_date: date
    end_date: date
    
    # Evidence
    sanction_reference: str  # e.g., 'OFFLINE_LEAF_NO_123'
    evidence_file_url: Optional[str] = None
    consistency_outcome: str  # 'SYNCHRONIZED', 'INCONSISTENT'
    
    created_at: date = models.Field(default=date.today)
    updated_at: date = models.Field(default=date.today)


class SLAConfig(models.Model):
    """
    Scheduled work plan configuration for reminders and escalations.
    
    Responsibilities:
    - Store threshold values and escalation actions.
    - Used by event-triggered processing (Celery jobs).
    """
    class Meta:
        app_label = 'leave'
        ordering = []

    # Thresholds
    reminder_threshold_hours: int = models.IntegerField(default=24)
    escalation_threshold_hours: int = models.IntegerField(default=72)
    
    # Actions
    reminder_action: str  # e.g., 'SEND_EMAIL', 'LOG'
    escalation_action: str  # e.g., 'REASSIGN_TASK', 'NOTIFY_SUPERVISOR'
    
    updated_at: date = models.Field(default=date.today)
