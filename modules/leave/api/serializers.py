"""DRF serializers for the Leave module."""

from rest_framework import serializers

from modules.leave.models import (
    HierarchyConfig,
    HolidayRHCalendar,
    LeaveAccount,
    LeaveLedgerEntry,
    LeavePolicyConfig,
    LeaveRequest,
    OfflineSanctionRecord,
    RequestAction,
    ResumptionRecord,
    SLAConfig,
    SubstituteAssignment,
    WorkflowTask,
)


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_user_id = serializers.IntegerField(source="user_id", required=False)
    submitted_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = (
            "id",
            "employee_user_id",
            "category",
            "start_date",
            "end_date",
            "purpose",
            "station_leave_details",
            "status",
            "submitted_at",
            "substitute_user_id",
            "has_substitute",
            "is_cancelled",
        )
        read_only_fields = ("id", "status", "submitted_at", "has_substitute", "is_cancelled")

    def validate(self, attrs):
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError("start_date must not be after end_date")
        if attrs["category"] not in {"CL", "RH", "SCL", "EL", "COL", "VL"}:
            raise serializers.ValidationError("Unsupported leave category")
        return attrs


class WorkflowTaskSerializer(serializers.ModelSerializer):
    request_reference = serializers.IntegerField(source="request_id_id", read_only=True)

    class Meta:
        model = WorkflowTask
        fields = (
            "id",
            "request_reference",
            "task_kind",
            "assigned_user_id",
            "state",
            "due_date",
            "reminder_sent",
            "escalation_triggered",
        )
        read_only_fields = (
            "id",
            "request_reference",
            "state",
            "reminder_sent",
            "escalation_triggered",
        )


class RequestActionSerializer(serializers.ModelSerializer):
    request_reference = serializers.IntegerField(source="request_id_id", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = RequestAction
        fields = (
            "id",
            "request_reference",
            "actor_user_id",
            "action_type",
            "outcome",
            "reason",
            "timestamp",
        )
        read_only_fields = ("id", "request_reference", "timestamp")


class LeaveAccountSerializer(serializers.ModelSerializer):
    employee_user_id = serializers.IntegerField(source="user_id", read_only=True)

    class Meta:
        model = LeaveAccount
        fields = ("id", "employee_user_id", "category", "year", "balance", "is_faculty")
        read_only_fields = fields


class LeaveLedgerEntrySerializer(serializers.ModelSerializer):
    request_reference = serializers.IntegerField(source="reference_request_id", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = LeaveLedgerEntry
        fields = (
            "id",
            "user_id",
            "category",
            "year",
            "entry_type",
            "amount",
            "request_reference",
            "reason",
            "timestamp",
        )
        read_only_fields = fields


class SubstituteAssignmentSerializer(serializers.ModelSerializer):
    request_reference = serializers.IntegerField(source="request_id_id", read_only=True)

    class Meta:
        model = SubstituteAssignment
        fields = (
            "id",
            "request_reference",
            "applicant_user_id",
            "substitute_user_id",
            "response",
            "responsibility_interval_start",
            "responsibility_interval_end",
        )
        read_only_fields = ("id", "request_reference", "applicant_user_id", "response")


class LeavePolicyConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeavePolicyConfig
        fields = ("id", "category", "annual_entitlement", "counting_rule", "carry_forward_allowed")
        read_only_fields = ("id",)


class HierarchyConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = HierarchyConfig
        fields = (
            "id",
            "unit_head_role",
            "establishment_step_required",
            "establishment_role",
            "director_self_sanction",
        )
        read_only_fields = ("id",)


class HolidayRHCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = HolidayRHCalendar
        fields = (
            "id",
            "name",
            "publication_date",
            "effective_from",
            "effective_to",
            "is_published",
            "restricted_holidays",
            "holiday_markers",
        )
        read_only_fields = ("id",)


class ResumptionRecordSerializer(serializers.ModelSerializer):
    request_reference = serializers.IntegerField(source="request_id_id", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ResumptionRecord
        fields = (
            "id",
            "request_reference",
            "actual_start_date",
            "review_status",
            "review_outcome",
            "timestamp",
        )
        read_only_fields = (
            "id",
            "request_reference",
            "review_status",
            "review_outcome",
            "timestamp",
        )


class OfflineSanctionRecordSerializer(serializers.ModelSerializer):
    source_leave_transaction_id = serializers.IntegerField(
        source="source_transaction_id", read_only=True
    )
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = OfflineSanctionRecord
        fields = (
            "id",
            "employee_user_id",
            "category",
            "interval_start",
            "interval_end",
            "sanction_reference",
            "consistency_outcome",
            "source_leave_transaction_id",
            "timestamp",
        )
        read_only_fields = ("id", "consistency_outcome", "source_leave_transaction_id", "timestamp")


class SLAConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAConfig
        fields = (
            "id",
            "reminder_threshold_hours",
            "escalation_threshold_hours",
            "escalation_action",
        )
        read_only_fields = ("id",)


class LeaveBalanceSerializer(serializers.Serializer):
    employee_user_id = serializers.IntegerField()
    accounts = LeaveAccountSerializer(many=True)
