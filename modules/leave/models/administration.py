"""
Administration Models for Employee Leave Management (ELM).

This module contains aggregates and domain models for administrative leave operations,
including offline-sanctioned leave synchronization, authorized record maintenance,
and policy/hierarchy configuration.

Per BR-EL-037: Administrative maintenance is distinct from sanctioning workflows.
Per PS v1.4 §5/12: Policy parameters use current configured values without draft/publish/effective-version lifecycle.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from django.db import models
from fusion_auth.client import get_client
from modules.directory.models import UserRef
from modules.leave.contracts import EmployeeDTO


# =============================================================================
# 1. Offline Sanction Record (EL-UC-016)
# Purpose: Synchronize already-sanctioned offline/paper leave without triggering
# a new approval workflow.
# =============================================================================

class OfflineSanctionRecord(models.Model):
    """
    Represents an already-sanctioned leave that was handled via offline/paper process.
    Used to synchronize ELM records (EL-UC-016) without issuing a second sanction.
    
    Constraints:
    - No workflow initiation upon creation (BR-EL-029).
    - Requires evidence of prior sanction and record consistency validation.
    """

    # Core Identity
    id = models.BigAutoField(primary_key=True)
    employee_user_id = models.IntegerField(
        db_index=True,
        help_text="IAM user ID of the employee (per contracts.py).",
    )
    category = models.CharField(max_length=20, choices=[('CL', 'Casual'), ('RH', 'Restricted Holiday')])

    # Sanction Details
    start_date = models.DateField()
    end_date = models.DateField()
    sanction_reference_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reference ID from the offline sanction document (e.g., HR file number).",
    )
    evidence_notes = models.TextField(
        blank=True,
        help_text="Notes regarding the source of the sanction and consistency validation."
    )

    # Synchronization Outcome
    status = models.CharField(max_length=20, default='synced', choices=[('synced', 'Synchronized'), ('pending_validation', 'Pending Validation')])
    balance_adjustment_applied = models.BooleanField(
        default=True,
        help_text="Whether the leave balance was adjusted upon synchronization."
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'leave_offline_sanction_records'
        unique_together = ('employee_user_id', 'start_date', 'end_date')

    def __str__(self):
        return f"Offline Sanction: {self.employee_user_id} ({self.category}) {self.start_date}-{self.end_date}"


# =============================================================================
# 2. Authorized Leave Record Maintenance (EL-UC-017)
# Purpose: Allow authorized administrators to correct/maintain leave records
# without triggering sanctioning workflows.
# =============================================================================

class LeaveRecordMaintenance(models.Model):
    """
    Tracks administrative maintenance actions on existing leave records.
    Distinguishes from sanctioning by ensuring no new workflow is initiated.
    
    Constraints:
    - Actor must have specific record-maintenance authorization (BR-EL-036).
    - Changes are logged but do not re-evaluate policy for approval.
    """

    id = models.BigAutoField(primary_key=True)
    leave_request_id = models.IntegerField(
        db_index=True,
        help_text="ID of the LeaveRequest being maintained."
    )
    actor_user_id = models.IntegerField(
        db_index=True,
        help_text="IAM user ID of the administrator performing maintenance."
    )
    action_type = models.CharField(max_length=50, choices=[('correction', 'Correction'), ('update', 'Update')])
    field_modified = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    reason = models.TextField(
        blank=True,
        help_text="Reason for the administrative maintenance action."
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'leave_record_maintenance_logs'

    def __str__(self):
        return f"Maint: {self.leave_request_id} by {self.actor_user_id} ({self.action_type})"


# =============================================================================
# 3. Leave Policy Configuration (PS v1.4 §5/12)
# Purpose: Store current configured leave entitlements and parameters.
# No draft/publish/effective-version lifecycle.
# =============================================================================

class LeavePolicyConfig(models.Model):
    """
    Current configuration of leave policies and entitlements.
    
    Per PS v1.4 §§5 & 12: Uses current configured values directly.
    No draft/publish/effective-version lifecycle applies to parameters.
    """

    id = models.BigAutoField(primary_key=True)
    # Entitlements (per BR-EL-002, BR-EL-003)
    casual_leave_days_per_year = models.IntegerField(default=8, help_text="Default CL days per year.")
    restricted_holiday_days_per_year = models.IntegerField(default=2, help_text="Default RH days per year.")
    
    # Category-specific overrides (optional)
    faculty_cl_override = models.BooleanField(default=False, help_text="Override CL days for faculty?")
    faculty_cl_days = models.IntegerField(blank=True, null=True, help_text="Faculty specific CL days.")
    
    # Year-end behavior
    carry_forward_eligible = models.BooleanField(
        default=False,
        help_text="Allow unused leave to carry forward to next year?"
    )
    
    # Hierarchy Configuration (BR-EL-030)
    requires_unit_head_review = models.BooleanField(default=True)
    requires_director_approval = models.BooleanField(default=False)
    director_self_sanction_allowed = models.BooleanField(
        default=False,
        help_text="Allow Director to self-sanction if no higher authority exists (BR-EL-020)."
    )
    
    # SLA Configuration (BR-EL-038)
    sla_reminder_threshold_hours = models.IntegerField(default=48, help_text="Hours before reminder.")
    sla_escalation_threshold_hours = models.IntegerField(default=72, help_text="Hours before escalation.")
    
    # Timestamps (for audit of config changes)
    last_modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'leave_policy_config'
        unique_together = ('id',)

    def __str__(self):
        return f"Policy Config: {self.casual_leave_days_per_year} CL / {self.restricted_holiday_days_per_year} RH"


# =============================================================================
# 4. Hierarchy Configuration (BR-EL-030)
# Purpose: Store org-unit/designation routing facts.
# =============================================================================

class HierarchyConfig(models.Model):
    """
    Current routing configuration for leave approval hierarchy.
    
    Per PS v1.4 §5/12: Uses current configured values directly.
    """

    id = models.BigAutoField(primary_key=True)
    # Routing Rules
    unit_head_required = models.BooleanField(default=True)
    director_required = models.BooleanField(default=False)
    establishment_routing_enabled = models.BooleanField(
        default=False,
        help_text="Optional Establishment step in routing (BR-EL-014)."
    )
    
    # Designation-based overrides
    requires_director_for_designations = models.JSONField(
        blank=True,
        null=True,
        help_text="List of designations requiring Director approval."
    )
    
    # Timestamps
    last_modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'leave_hierarchy_config'
        unique_together = ('id',)

    def __str__(self):
        return f"Hierarchy Config: Unit Head {'Yes' if self.unit_head_required else 'No'}"


# =============================================================================
# 5. SLA Configuration (BR-EL-038)
# Purpose: Configure reminder and escalation thresholds.
# =============================================================================

class SLAConfig(models.Model):
    """
    Configuration for SLA processing thresholds.
    
    Per PS v1.4 §5/12: Uses current configured values directly.
    """

    id = models.BigAutoField(primary_key=True)
    reminder_threshold_hours = models.IntegerField(default=48, help_text="Hours before task due for reminder.")
    escalation_threshold_hours = models.IntegerField(default=72, help_text="Hours before task due for escalation.")
    
    # Escalation Action
    escalation_action_type = models.CharField(
        max_length=50,
        default='notify',
        choices=[('notify', 'Notification'), ('reroute', 'Reroute')],
        help_text="Action taken when threshold is breached."
    )
    
    # Timestamps
    last_modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'sla_config'
        unique_together = ('id',)

    def __str__(self):
        return f"SLA Config: {self.reminder_threshold_hours}h / {self.escalation_threshold_hours}h"


# =============================================================================
# 6. Holiday/RH Calendar Administration (EL-UC-015)
# Purpose: Manage publication state of holiday calendars.
# Per BR-EL-031: Only currently effective published calendar is used for validation.
# =============================================================================

class HolidayRHCalendar(models.Model):
    """
    Represents a published holiday or Restricted Holiday calendar.
    
    Constraints:
    - Only the 'published' state is considered effective for validation (BR-EL-031).
    - Publication itself is supported; prior states are retained for audit.
    """

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, help_text="Calendar name (e.g., 'Academic Year 2026-27').")
    year = models.IntegerField(help_text="Year of the calendar.")
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Holiday Data (simplified; can be expanded)
    holidays = models.JSONField(
        blank=True,
        null=True,
        help_text="List of {date: str, type: str} holiday entries."
    )
    
    # Publication State
    is_published = models.BooleanField(default=False, help_text="Is this calendar currently effective?")
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'holiday_rh_calendars'
        unique_together = ('year',)

    def __str__(self):
        return f"{self.name} ({self.year})"


# =============================================================================
# 7. Resumption Record (EL-UC-010, EL-UC-011)
# Purpose: Track actual resumption of duty and review outcomes.
# Per BR-EL-028: Normal/early/late resumption outcomes.
# =============================================================================

class ResumptionRecord(models.Model):
    """
    Records the actual resumption of duty for ongoing leave (EL/COL/VL).
    
    Constraints:
    - Supported only for EL, COL, VL categories (BR-EL-027).
    - Review outcome determines balance adjustment (BR-EL-028).
    """

    id = models.BigAutoField(primary_key=True)
    leave_request_id = models.IntegerField(
        db_index=True,
        help_text="ID of the original approved LeaveRequest."
    )
    employee_user_id = models.IntegerField(
        db_index=True,
        help_text="IAM user ID of the employee."
    )
    
    # Actual Return Details
    actual_start_date = models.DateField()
    actual_end_date = models.DateField()
    
    # Review Outcome
    review_status = models.CharField(
        max_length=50,
        default='pending',
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
    )
    outcome_notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'resumption_records'

    def __str__(self):
        return f"Resumption: {self.leave_request_id} ({self.actual_start_date}-{self.actual_end_date})"


# =============================================================================
# 8. Substitute Assignment (EL-UC-002, EL-UC-019)
# Purpose: Track substitute consent and replacement nomination.
# Per BR-EL-011–012: Applicant differs from substitute; substitute must be eligible.
# =============================================================================

@dataclass(frozen=True)
class SubstituteAssignmentDTO:
    """
    Projection for substitute assignment details.
    Used by services to validate eligibility and consent.
    """
    request_id: int
    applicant_user_id: int  # The employee requesting leave
    substitute_user_id: int  # The nominated substitute
    response_status: str  # 'accepted', 'declined', 'pending'
    responsibility_interval: Optional[tuple[date, date]] = None
    
    @classmethod
    def from_model(cls, model_instance):
        return cls(
            request_id=model_instance.leave_request_id,
            applicant_user_id=model_instance.applicant_user_id,
            substitute_user_id=model_instance.substitute_user_id,
            response_status=model_instance.response_status,
            responsibility_interval=(
                model_instance.responsibility_start_date,
                model_instance.responsibility_end_date
            ) if model_instance.responsibility_start_date else None
        )


class SubstituteAssignment(models.Model):
    """
    Tracks substitute assignments and consent.
    
    Constraints:
    - Substitute must be an eligible employee (BR-EL-011).
    - Cannot overlap with pending/approved leave (domain logic in services).
    """

    id = models.BigAutoField(primary_key=True)
    leave_request_id = models.IntegerField(
        db_index=True,
        help_text="ID of the LeaveRequest requiring a substitute."
    )
    applicant_user_id = models.IntegerField(
        db_index=True,
        help_text="IAM user ID of the employee requesting leave."
    )
    substitute_user_id = models.IntegerField(
        db_index=True,
        help_text="IAM user ID of the nominated substitute."
    )
    
    # Consent Status
    response_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')],
    )
    
    # Responsibility Interval (if applicable)
    responsibility_start_date = models.DateField(null=True, blank=True)
    responsibility_end_date = models.DateField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'substitute_assignments'

    def __str__(self):
        return f"Sub: {self.applicant_user_id} -> {self.substitute_user_id}"


# =============================================================================
# 9. Request Action History (EL-UC-001, EL-UC-003)
# Purpose: Append-oriented action history for user-visible status.
# =============================================================================

class RequestAction(models.Model):
    """
    Records actions taken on leave requests by actors.
    
    Constraints:
    - Append-only (no in-place modification of history).
    - Includes reason/evidence reference where applicable.
    """

    id = models.BigAutoField(primary_key=True)
    leave_request_id = models.IntegerField(
        db_index=True,
        help_text="ID of the LeaveRequest."
    )
    actor_user_id = models.IntegerField(
        db_index=True,
        help_text="IAM user ID of the actor performing the action."
    )
    
    # Action Details
    action_type = models.CharField(max_length=50, choices=[('submit', 'Submit'), ('review', 'Review'), ('approve', 'Approve'), ('reject', 'Reject'), ('cancel', 'Cancel')])
    outcome = models.CharField(max_length=50, blank=True)
    reason = models.TextField(blank=True)
    evidence_reference = models.CharField(max_length=200, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'request_action_history'

    def __str__(self):
        return f"Action: {self.action_type} by {self.actor_user_id}"


# =============================================================================
# 10. Leave Ledger Entry (EL-UC-020)
# Purpose: Explicit entries for balance changes.
# Per BR-EL-002, BR-EL-003: Balances derived/maintained via explicit entries.
# =============================================================================

@dataclass(frozen=True)
class LedgerEntryDTO:
    """
    Projection for ledger entry details.
    """
    entry_id: int
    employee_user_id: int
    category: str
    transaction_type: str  # 'approve', 'cancel', 'extend', 'resumption_adjustment', etc.
    amount: int
    reference_source: str  # 'request', 'year_end', 'offline_sync'
    timestamp: date


class LeaveLedgerEntry(models.Model):
    """
    Records explicit transactions affecting leave balances.
    
    Constraints:
    - Concurrency-sensitive balance changes use transactions/locking (handled in services).
    """

    id = models.BigAutoField(primary_key=True)
    employee_user_id = models.IntegerField(
        db_index=True,
        help_text="IAM user ID of the employee."
    )
    category = models.CharField(max_length=20, choices=[('CL', 'Casual'), ('RH', 'Restricted Holiday')])
    
    # Transaction Details
    transaction_type = models.CharField(
        max_length=50,
        help_text="Type of transaction (e.g., APPROVE, CANCEL, EXTEND)."
    )
    amount = models.IntegerField(help_text="Number of days affected.")
    
    # Reference
    reference_source = models.CharField(
        max_length=50,
        help_text="Source of the transaction (e.g., 'request', 'year_end')."
    )
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'leave'
        db_table = 'leave_ledger_entries'

    def __str__(self):
        return f"Ledger: {self.employee_user_id} ({self.category}) {self.transaction_type}"


# =============================================================================
# 11. Leave Account (EL-UC-020)
# Purpose: Aggregate balance view.
# Note: Balance is derived from ledger entries; this model provides the aggregate view.
# =============================================================================

@dataclass(frozen=True)
class LeaveAccountDTO:
    """
    Projection for leave account balance.
    """
    employee_user_id: int
    category: str
    available_days: int
    used_days: int
    total_entitlement: int


class LeaveAccount(models.Model):
    """
    Provides the current state of leave balances.
    
    Note: Actual balance calculation is performed via services using ledger entries.
    This model may store cached balances for performance if required by specific constraints.
    """

    id = models.BigAutoField(primary_key=True)
    employee_user_id = models.IntegerField(
        db_index=True,
        help_text="IAM user ID of the employee."
    )
    category = models.CharField(max_length=20, choices=[('CL', 'Casual'), ('RH', 'Restricted Holiday')])
    
    # Cached Balances (optional; services should calculate if needed)
    available_days = models.IntegerField(default=0)
    used_days = models.IntegerField(default=0)
    total_entitlement = models.IntegerField(default=0)
    
    class Meta:
        app_label = 'leave'
        db_table = 'leave_accounts'

    def __str__(self):
        return f"Account: {self.employee_user_id} ({self.category})"
