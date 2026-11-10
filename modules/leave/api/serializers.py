"""
Employee Leave Management (ELM) — API Serializers.

Thin, transport-layer validation mirroring domain models and approved endpoints.
No business policy logic resides here; all rules are enforced in services or domain layers.
Identity references are integer user_id values. Cross-module data access uses public contracts from modules.leave.contracts.
"""
from __future__ import annotations

from typing import Any, Optional

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

# -- Public Contracts (via modules.leave.contracts) --
try:
    from modules.leave.contracts import EmployeeDTO, VacationPeriodDTO
except ImportError:
    # Fallback for local development if contracts module is not yet fully wired
    class EmployeeDTO:
        user_id: int
        username: str
        display_name: str
        kind: str
        email: str = ""
        department: str = ""
        designation: str = ""
        batch_year: int | None = None
    
    class VacationPeriodDTO:
        id: int
        start_date: str
        end_date: str
        is_active: bool = False

# -- Leave Request Serializer --
class LeaveRequestSerializer(serializers.ModelSerializer):
    """Serializes a LeaveRequest aggregate for read/write operations.

Validates transport layer constraints (dates, non-empty fields).
Business rules (balance checks, overlap detection) are enforced in services.
"""

    # -- Core Fields --
    employee_user_id = serializers.IntegerField(required=True, min_value=1)
    category = serializers.CharField(max_length=20, required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    purpose = serializers.CharField(max_length=500, required=False, allow_blank=True)
    station_leave_details = serializers.JSONField(required=False, allow_null=True)
    substitute_user_id = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    
    # -- Computed/Read-Only Fields --
    submitted_at = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(max_length=50, read_only=True)
    linked_original_request = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = "LeaveRequest"
        fields = (
            "id", "employee_user_id", "category", "start_date", "end_date",
            "purpose", "station_leave_details", "substitute_user_id",
            "submitted_at", "status", "linked_original_request"
        )
        read_only_fields = (
            "id", "submitted_at", "status", "linked_original_request"
        )
        # Explicit allow-list prevents accidental inclusion of internal fields

# -- Workflow Task Serializer --
class WorkflowTaskSerializer(serializers.ModelSerializer):
    """Serializes a WorkflowTask for tracking actionable assignments.

Tracks state, assignment details, and timestamps without business logic.
"""

    request_reference = serializers.IntegerField(required=True)
    task_kind = serializers.CharField(max_length=100, required=True)
    assigned_user_id = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    state = serializers.CharField(max_length=50, read_only=True)
    due_date = serializers.DateField(required=False, allow_null=True)
    reminder_sent_at = serializers.DateTimeField(read_only=True)
    escalation_triggered_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = "WorkflowTask"
        fields = (
            "id", "request_reference", "task_kind", "assigned_user_id",
            "state", "due_date", "reminder_sent_at", "escalation_triggered_at"
        )
        read_only_fields = (
            "id", "state", "reminder_sent_at", "escalation_triggered_at"
        )

# -- Request Action / History Serializer --
class RequestActionSerializer(serializers.ModelSerializer):
    """Serializes an action taken on a LeaveRequest.

Append-only history for auditing and user visibility.
"""

    request_reference = serializers.IntegerField(required=True)
    actor_user_id = serializers.IntegerField(required=True, min_value=1)
    action_type = serializers.CharField(max_length=50, required=True)
    outcome = serializers.CharField(max_length=200, required=False, allow_blank=True)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    evidence_reference = serializers.CharField(max_length=300, required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = "RequestAction"
        fields = (
            "id", "request_reference", "actor_user_id", "action_type",
            "outcome", "reason", "evidence_reference", "timestamp"
        )
        read_only_fields = (
            "id", "timestamp"
        )

# -- Leave Account / Ledger Entry Serializer --
class LeaveAccountSerializer(serializers.ModelSerializer):
    """Serializes a LeaveAccount aggregate for balance viewing.

Balances are derived from ledger entries; this serializer exposes the current state.
"""

    employee_user_id = serializers.IntegerField(required=True, min_value=1)
    category = serializers.CharField(max_length=20, required=True)
    balance = serializers.FloatField(read_only=True)
    year_end_balance = serializers.FloatField(read_only=True)
    
    class Meta:
        model = "LeaveAccount"
        fields = (
            "id", "employee_user_id", "category", "balance", "year_end_balance"
        )
        read_only_fields = (
            "id", "balance", "year_end_balance"
        )

class LeaveLedgerEntrySerializer(serializers.ModelSerializer):
    """Serializes a single LedgerEntry for audit and adjustment visibility.

"""

    entry_type = serializers.CharField(max_length=50, required=True)
    amount = serializers.FloatField(required=True)
    request_reference = serializers.IntegerField(required=False, allow_null=True)
    year_end_source = serializers.BooleanField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = "LeaveLedgerEntry"
        fields = (
            "id", "entry_type", "amount", "request_reference",
            "year_end_source", "timestamp"
        )
        read_only_fields = (
            "id", "timestamp"
        )

# -- Substitute Assignment Serializer --
class SubstituteAssignmentSerializer(serializers.ModelSerializer):
    """Serializes a SubstituteAssignment for consent and routing.

Ensures applicant != substitute and eligibility constraints are met at service layer.
"""

    request_reference = serializers.IntegerField(required=True)
    applicant_user_id = serializers.IntegerField(required=True, min_value=1)
    substitute_user_id = serializers.IntegerField(required=True, min_value=1)
    responsibility_interval_start = serializers.DateField(required=True)
    responsibility_interval_end = serializers.DateField(required=True)
    response = serializers.CharField(max_length=50, required=True)
    
    class Meta:
        model = "SubstituteAssignment"
        fields = (
            "id", "request_reference", "applicant_user_id", "substitute_user_id",
            "responsibility_interval_start", "responsibility_interval_end",
            "response"
        )

# -- Leave Policy Config Serializer --
class LeavePolicyConfigSerializer(serializers.Serializer):
    """Serializes current Leave Policy configuration.

Per Problem Statement v1.4: uses current configured values only.
No draft/publish/effective-version lifecycle fields are included.
"""

    class Meta:
        fields = []  # No model mapping; purely config data

    cl_entitlement = serializers.IntegerField(required=True, min_value=0)
    rh_entitlement = serializers.IntegerField(required=True, min_value=0)
    scl_entitlement = serializers.IntegerField(required=True, min_value=0)
    el_entitlement = serializers.IntegerField(required=True, min_value=0)
    col_entitlement = serializers.IntegerField(required=True, min_value=0)
    vl_entitlement = serializers.IntegerField(required=True, min_value=0)
    cl_half_days = serializers.BooleanField(default=False)
    
# -- Hierarchy Config Serializer --
class HierarchyConfigSerializer(serializers.Serializer):
    """Serializes current Hierarchy routing configuration.

Stores org-unit/designation/category routing facts.
"""

    class Meta:
        fields = []  # No model mapping; purely config data

    unit_head_role = serializers.CharField(max_length=100, required=True)
    establishment_step_required = serializers.BooleanField(default=False)
    director_self_sanction = serializers.BooleanField(default=False)
    sanctioned_roles = serializers.ListField(child=serializers.CharField(), required=False, allow_blank=True)

# -- Holiday/RH Calendar Serializer --
class HolidayRHCalendarSerializer(serializers.ModelSerializer):
    """Serializes a published Holiday/RH calendar entry.

Only currently effective published calendars are used for validation.
"""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100, required=True)
    date = serializers.DateField(required=True)
    is_restricted_holiday = serializers.BooleanField(default=False)
    publication_state = serializers.CharField(max_length=20, read_only=True)
    published_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = "HolidayRHCalendar"
        fields = (
            "id", "name", "date", "is_restricted_holiday",
            "publication_state", "published_at"
        )
        read_only_fields = (
            "id", "publication_state", "published_at"
        )

# -- Resumption Record Serializer --
class ResumptionRecordSerializer(serializers.ModelSerializer):
    """Serializes a ResumptionRecord for early/late return handling.

Supported only for EL/COL/VL categories.
"""

    request_reference = serializers.IntegerField(required=True)
    actual_resumption_date = serializers.DateField(required=True)
    required_details = serializers.JSONField(required=False, allow_null=True)
    review_status = serializers.CharField(max_length=20, read_only=True)
    reviewed_outcome = serializers.CharField(max_length=200, read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = "ResumptionRecord"
        fields = (
            "id", "request_reference", "actual_resumption_date",
            "required_details", "review_status", "reviewed_outcome", "timestamp"
        )
        read_only_fields = (
            "id", "review_status", "reviewed_outcome", "timestamp"
        )

# -- Offline Sanction Record Serializer --
class OfflineSanctionRecordSerializer(serializers.ModelSerializer):
    """Serializes an OfflineSanctionRecord for paper/offline leave synchronization.

Does not issue a second sanction; records the consistency outcome.
"""

    employee_user_id = serializers.IntegerField(required=True, min_value=1)
    category = serializers.CharField(max_length=20, required=True)
    interval_start = serializers.DateField(required=True)
    interval_end = serializers.DateField(required=True)
    sanction_reference = serializers.CharField(max_length=100, required=True)
    consistency_outcome = serializers.CharField(max_length=50, read_only=True)
    source_leave_transaction_id = serializers.IntegerField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = "OfflineSanctionRecord"
        fields = (
            "id", "employee_user_id", "category", "interval_start",
            "interval_end", "sanction_reference", "consistency_outcome",
            "source_leave_transaction_id", "timestamp"
        )
        read_only_fields = (
            "id", "consistency_outcome", "source_leave_transaction_id", "timestamp"
        )

# -- SLA Config Serializer --
class SLAConfigSerializer(serializers.Serializer):
    """Serializes SLA threshold configuration.

Used by event-triggered SLA processing; current values apply.
"""

    class Meta:
        fields = []  # No model mapping; purely config data

    reminder_threshold_hours = serializers.IntegerField(required=True, min_value=1)
    escalation_threshold_hours = serializers.IntegerField(required=True, min_value=1)
    escalation_action = serializers.CharField(max_length=100, required=True)
