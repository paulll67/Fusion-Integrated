"""Leave request aggregate and lifecycle management.

This module implements the core LeaveRequest aggregate, including Station Leave fields,
substitute response handling, approval/action history, cancellation, extension,
and resumption records as supported by the ELM specifications (v1.4/v1.5).

Workflow authority: 06_ELM_Workflow_Specifications_v1.6_FINAL.docx
Policy configuration: Follows Problem Statement v1.4 (current values only, no lifecycle).
Identity references: Integer user_id values; cross-module data uses public contracts.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from django.db import models
from django.core.validators import MinValueValidator
from core.db.mixins import TimeStampedModel, UserScopedModel
from modules.directory.contracts import get_employees
from modules.leave.contracts import EmployeeDTO


class LeaveCategory(models.TextChoices):
    CASUAL_LEAVE = "CL", "Casual Leave"
    RESTRICTED_HOLIDAY = "RH", "Restricted Holiday"
    SPECIAL_CASUAL_LEAVE = "SCL", "Special Casual Leave"
    EARNED_LEAVE = "EL", "Earned Leave"
    COMPUTED_OVERTIME_LEAVE = "COL", "Computed Overtime Leave"
    VACATION_LEAVE = "VL", "Vacation Leave"


class RequestStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    AWAITING_SUBSTITUTE_RESPONSE = "awaiting_substitute_response", "Awaiting Substitute Response"
    AWAITING_UNIT_HEAD_REVIEW = "awaiting_unit_head_review", "Awaiting Unit Head Review"
    AWAITING_HIGHER_SANCTION = "awaiting_higher_sanction", "Awaiting Higher Sanction"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"
    CANCELLED = "cancelled", "Cancelled"
    EXTENDED = "extended", "Extended"
    RESUMPTION_REVIEW_PENDING = "resumption_review_pending", "Resumption Review Pending"
    YEAR_END_PROCESSED = "year_end_processed", "Year End Processed"


class RequestAction(models.TextChoices):
    SUBMIT = "submit", "Submit"
    ACCEPT_SUBSTITUTE = "accept_substitute", "Accept Substitute"
    DECLINE_SUBSTITUTE = "decline_substitute", "Decline Substitute"
    NOMINATE_REPLACEMENT = "nominate_replacement", "Nominate Replacement"
    UNIT_HEAD_APPROVE = "unit_head_approve", "Unit Head Approve"
    UNIT_HEAD_REJECT = "unit_head_reject", "Unit Head Reject"
    HIGHER_SANCTION_APPROVE = "higher_sanction_approve", "Higher Sanction Approve"
    HIGHER_SANCTION_REJECT = "higher_sanction_reject", "Higher Sanction Reject"
    WITHDRAW = "withdraw", "Withdraw"
    CANCEL = "cancel", "Cancel"
    EXTEND = "extend", "Extend"
    RESUME_SUBMIT = "resume_submit", "Resume Submit"
    RESUME_REVIEW_APPROVE = "resume_review_approve", "Resume Review Approve"
    RESUME_REJECT = "resume_review_reject", "Resume Review Reject"


class StationLeaveType(models.TextChoices):
    INTRA_DEPT = "intra_dept", "Intra-Department"
    INTER_DEPT = "inter_dept", "Inter-Department"
    INTER_ORG = "inter_org", "Inter-Org"


class RequestActionHistory(models.Model):
    """Append-only action history for leave requests.

    Tracks every state transition and operation performed on a request.
    """

    request = models.ForeignKey(
        "LeaveRequest",
        on_delete=models.CASCADE,
        related_name="action_history",
    )
    actor_user_id = models.IntegerField()
    action_label = models.CharField(max_length=100)
    action_outcome = models.CharField(max_length=200, blank=True)
    reason = models.TextField(blank=True)
    evidence_ref = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "leave_request_action_history"
        indexes = [models.Index(fields=["request", "timestamp"])]

    def __str__(self):
        return f"{self.request.id}: {self.action_label} by {self.actor_user_id}"


class LeaveRequest(TimeStampedModel, UserScopedModel):
    """Leave request aggregate.

    Represents a single leave application lifecycle. Fields are frozen at submission
    except for specific actions (extension, resumption) which create new records
    or modify existing ones via history/ledger entries.
    """

    STATUS_CHOICES = RequestStatus.choices
    CATEGORY_CHOICES = LeaveCategory.choices
    ACTION_CHOICES = RequestActionHistory.choices
    STATION_LEAVE_TYPE_CHOICES = StationLeaveType.choices

    # Core identity and lifecycle
    employee_user_id = models.IntegerField()
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=RequestStatus.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Period details
    start_date = models.DateField()
    end_date = models.DateField()
    duration_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Calculated from start/end dates",
    )
    half_day_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Count of half-day leaves (CL only)",
    )

    # Purpose and details
    purpose = models.TextField(blank=True)
    station_leave_type = models.CharField(max_length=20, choices=STATION_LEAVE_TYPE_CHOICES, blank=True)
    
    # Station Leave specific fields
    intra_dept_days = models.PositiveIntegerField(default=0)
    inter_dept_days = models.PositiveIntegerField(default=0)
    inter_org_days = models.PositiveIntegerField(default=0)
    
    # Substitute management
    substitute_user_id: Optional[int] = None
    substitute_response_status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("declined", "Declined"),
        ],
        default="pending",
    )
    replacement_user_id: Optional[int] = None
    
    # Links to related records
    extension_request: Optional["LeaveRequest"] = models.ForeignKey(
        "LeaveRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="base_requests",
    )
    resumption_record: Optional["ResumptionRecord"] = models.OneToOneField(
        "ResumptionRecord",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="original_request",
    )
    
    # Metadata
    created_by_user_id = models.IntegerField()
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "leave_requests"
        constraints = [
            models.UniqueConstraint(
                fields=["employee_user_id", "start_date", "end_date"],
                name="unique_leave_period_per_employee",
            ),
            models.CheckConstraint(
                check=models.Q(start_date__lte=end_date),
                name="valid_dates",
            ),
        ]
        indexes = [
            models.Index(fields=["employee_user_id", "status"]),
            models.Index(fields=["start_date"]),
        ]

    def __str__(self):
        return f"{self.id} {self.category} {self.status} {self.employee_user_id}"

    # --- Computed Properties ---

    @property
    def is_draft(self) -> bool:
        return self.status == RequestStatus.DRAFT

    @property
    def is_pending_substitute(self) -> bool:
        return self.status == RequestStatus.AWAITING_SUBSTITUTE_RESPONSE

    @property
    def is_pending_review(self) -> bool:
        return self.status in (
            RequestStatus.AWAITING_UNIT_HEAD_REVIEW,
            RequestStatus.AWAITING_HIGHER_SANCTION,
        )

    @property
    def is_approved(self) -> bool:
        return self.status == RequestStatus.APPROVED

    @property
    def is_cancelled(self) -> bool:
        return self.status == RequestStatus.CANCELLED

    @property
    def is_extended(self) -> bool:
        return self.status == RequestStatus.EXTENDED

    @property
    def is_resumption_pending(self) -> bool:
        return self.status == RequestStatus.RESUMPTION_REVIEW_PENDING

    # --- Validation Helpers ---

    def validate_dates(self) -> list[str]:
        """Validate start and end dates."""
        errors = []
        if self.start_date > self.end_date:
            errors.append("Start date must be before or equal to end date.")
        return errors

    def validate_substitute(self) -> list[str]:
        """Validate substitute eligibility and constraints."""
        errors = []
        if self.substitute_response_status == "pending":
            # Check if substitute overlaps with existing pending/approved leave
            try:
                sub_emp = get_employees([self.substitute_user_id])[self.substitute_user_id]
                if not sub_emp:
                    errors.append("Substitute employee not found or inactive.")
                else:
                    # TODO: Check overlap with other pending/approved leave for this substitute
                    # This requires access to LeaveAccount or similar, handled via contracts
                    pass
            except KeyError:
                errors.append("Substitute employee not found.")
        return errors

    def validate_category_eligibility(self) -> list[str]:
        """Check if category is supported."""
        errors = []
        # BR-EL-001: Only CL, RH, SCL, EL, COL, VL allowed
        if self.category not in (
            LeaveCategory.CASUAL_LEAVE,
            LeaveCategory.RESTRICTED_HOLIDAY,
            LeaveCategory.SPECIAL_CASUAL_LEAVE,
            LeaveCategory.EARNED_LEAVE,
            LeaveCategory.COMPUTED_OVERTIME_LEAVE,
            LeaveCategory.VACATION_LEAVE,
        ):
            errors.append(f"Unsupported leave category: {self.category}")
        return errors

    # --- Actions (Public API) ---

    def submit(self, created_by_user_id: int) -> "LeaveRequest":
        """Submit a new draft request."""
        if self.is_draft:
            self.status = RequestStatus.AWAITING_UNIT_HEAD_REVIEW
            self.submitted_at = datetime.now()
            # TODO: Validate dates, category, substitute before transition
            # If validation fails, raise an exception or return error message
            self.save(update_fields=["status", "submitted_at"])
        return self

    def accept_substitute(self, actor_user_id: int) -> "LeaveRequest":
        """Accept a substitute assignment."""
        if self.status == RequestStatus.AWAITING_SUBSTITUTE_RESPONSE:
            self.substitute_response_status = "accepted"
            # Transition based on BR-EL-015 and WF v1.6
            # If applicant is Director, might go to self-sanction path
            # Otherwise to Unit Head Review
            self.status = RequestStatus.AWAITING_UNIT_HEAD_REVIEW
            self.save(update_fields=["substitute_response_status", "status"])
        return self

    def decline_substitute(self, actor_user_id: int) -> "LeaveRequest":
        """Decline a substitute assignment."""
        if self.status == RequestStatus.AWAITING_SUBSTITUTE_RESPONSE:
            self.substitute_response_status = "declined"
            # Transition to Applicant Action Required (handled by workflow logic)
            # For now, we mark as pending replacement or withdrawal
            self.status = RequestStatus.DRAFT  # Allow re-submission with new substitute
            self.save(update_fields=["substitute_response_status", "status"])
        return self

    def nominate_replacement(self, actor_user_id: int) -> "LeaveRequest":
        """Nominate a replacement after decline."""
        if self.substitute_response_status == "declined" and not self.replacement_user_id:
            # Set the replacement user ID
            # TODO: Validate eligibility of replacement
            pass
        return self

    def unit_head_approve(self, actor_user_id: int) -> "LeaveRequest":
        """Record Unit Head approval."""
        if self.status in (
            RequestStatus.AWAITING_UNIT_HEAD_REVIEW,
            RequestStatus.AWAITING_SUBSTITUTE_RESPONSE,
        ):
            # Transition to Higher Sanction or Final Approval
            self.status = RequestStatus.AWAITING_HIGHER_SANCTION
            self.save(update_fields=["status"])
        return self

    def unit_head_reject(self, actor_user_id: int) -> "LeaveRequest":
        """Record Unit Head rejection."""
        if self.status == RequestStatus.AWAITING_UNIT_HEAD_REVIEW:
            self.status = RequestStatus.REJECTED
            self.save(update_fields=["status"])
        return self

    def higher_sanction_approve(self, actor_user_id: int) -> "LeaveRequest":
        """Record Higher Sanction approval."""
        if self.status == RequestStatus.AWAITING_HIGHER_SANCTION:
            self.status = RequestStatus.APPROVED
            self.save(update_fields=["status"])
        return self

    def higher_sanction_reject(self, actor_user_id: int) -> "LeaveRequest":
        """Record Higher Sanction rejection."""
        if self.status == RequestStatus.AWAITING_HIGHER_SANCTION:
            self.status = RequestStatus.REJECTED
            self.save(update_fields=["status"])
        return self

    def withdraw(self, actor_user_id: int) -> "LeaveRequest":
        """Withdraw a pending request."""
        if self.status in (
            RequestStatus.DRAFT,
            RequestStatus.AWAITING_UNIT_HEAD_REVIEW,
            RequestStatus.AWAITING_SUBSTITUTE_RESPONSE,
            RequestStatus.AWAITING_HIGHER_SANCTION,
        ):
            self.status = RequestStatus.WITHDRAWN
            self.save(update_fields=["status"])
        return self

    def cancel(self, actor_user_id: int) -> "LeaveRequest":
        """Cancel an approved leave before start."""
        if self.is_approved and self.start_date > datetime.now().date():
            # Restore balance logic handled in Ledger/Account layer
            self.status = RequestStatus.CANCELLED
            self.save(update_fields=["status"])
        return self

    def extend(self, actor_user_id: int) -> "LeaveRequest":
        """Start an extension request."""
        # Creates a new record linked to this one
        if self.status == RequestStatus.APPROVED:
            # TODO: Validate extension eligibility (BR-EL-025)
            # Create extension_request record
            pass
        return self

    def resume_submit(self, actor_user_id: int) -> "ResumptionRecord":
        """Submit actual resumption of duty."""
        if self.status == RequestStatus.APPROVED:
            # TODO: Validate resumption applicability (BR-EL-027)
            return ResumptionRecord.objects.create(
                request=self,
                actor_user_id=actor_user_id,
                actual_resumption_date=datetime.now().date(),
            )
        return None

    def resume_review_approve(self, actor_user_id: int) -> "ResumptionRecord":
        """Review and approve resumption."""
        if self.status == RequestStatus.RESUMPTION_REVIEW_PENDING:
            # Sync balance/period if early/late (BR-EL-028)
            return ResumptionRecord.objects.create(
                request=self,
                actor_user_id=actor_user_id,
                actual_resumption_date=datetime.now().date(),
                review_outcome="approved",
            )
        return None

    def resume_review_reject(self, actor_user_id: int) -> "ResumptionRecord":
        """Review and reject resumption."""
        if self.status == RequestStatus.RESUMPTION_REVIEW_PENDING:
            # Handle rejection logic (e.g., re-assign leave)
            return ResumptionRecord.objects.create(
                request=self,
                actor_user_id=actor_user_id,
                actual_resumption_date=datetime.now().date(),
                review_outcome="rejected",
            )
        return None

    # --- History Management ---

    def add_action_history(self, action_label: str, outcome: str = "", reason: str = "") -> RequestActionHistory:
        """Append an entry to the action history."""
        history = RequestActionHistory.objects.create(
            request=self,
            actor_user_id=self.employee_user_id,
            action_label=action_label,
            action_outcome=outcome,
            reason=reason,
        )
        return history

    # --- Station Leave Helpers ---

    def calculate_station_leave_days(self) -> int:
        """Calculate total station leave days based on type."""
        total = 0
        if self.station_leave_type == StationLeaveType.INTRA_DEPT:
            total += self.intra_dept_days
        elif self.station_leave_type == StationLeaveType.INTER_DEPT:
            total += self.inter_dept_days
        elif self.station_leave_type == StationLeaveType.INTER_ORG:
            total += self.inter_org_days
        return total

    def get_total_duration(self) -> int:
        """Get total duration in days."""
        if not self.duration_days:
            delta = self.end_date - self.start_date
            self.duration_days = delta.days + 1
        return self.duration_days


class ResumptionRecord(TimeStampedModel, UserScopedModel):
    """Record for resumption of duty review.

    Supported only for EL/COL/VL. Tracks actual return date and review outcome.
    """

    request = models.ForeignKey(
        "LeaveRequest",
        on_delete=models.CASCADE,
        related_name="resumption_records",
    )
    actor_user_id = models.IntegerField()
    actual_resumption_date = models.DateField()
    review_outcome = models.CharField(max_length=50, choices=[("approved", "Approved"), ("rejected", "Rejected")])
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "leave_resumption_records"
        indexes = [models.Index(fields=["request", "actual_resumption_date"])]

    def __str__(self):
        return f"Resumption {self.request.id}: {self.actual_resumption_date}"


class OfflineSanctionRecord(TimeStampedModel, UserScopedModel):
    """Record for already-sanctioned offline leave.

    Synchronizes an already-authorized paper/offline leave without issuing a second sanction.
    """

    employee_user_id = models.IntegerField()
    category = models.CharField(max_length=2, choices=LeaveCategory.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    reference_evidence = models.TextField()
    consistency_outcome = models.CharField(max_length=50, default="synchronized")

    class Meta:
        db_table = "leave_offline_sanction_records"
        indexes = [models.Index(fields=["employee_user_id", "start_date"])]

    def __str__(self):
        return f"Offline Sanction {self.employee_user_id}: {self.start_date} to {self.end_date}"


class SLAConfig(models.Model):
    """Configuration for SLA thresholds and escalation.

    Used by event-triggered SLA processing (UC-021).
    """

    reminder_threshold_hours = models.PositiveIntegerField(default=48)
    escalation_threshold_hours = models.PositiveIntegerField(default=72)
    escalation_action = models.CharField(max_length=200, default="notify")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "leave_sla_config"
        unique_together = ([],)  # Single global config

    def __str__(self):
        return f"SLA Config: {self.reminder_threshold_hours}h reminder, {self.escalation_threshold_hours}h escalation"
