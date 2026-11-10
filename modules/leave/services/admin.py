"""
Admin services for Employee Leave Management (ELM).

Handles policy/hierarchy configuration, holiday/RH calendar maintenance and publication,
online-sanctioned leave records, authorized leave record maintenance, and SLA threshold settings.

Identity references are integer user_id values. Cross-module data access uses public contracts from modules.leave.contracts.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction

from core.api.exceptions import ConflictError, NotFoundError
from fusion_auth.client import get_client
from modules.leave.contracts import HolidayRHCalendar
from modules.leave.models import (
    HierarchyConfig,
    LeavePolicyConfig,
)
from modules.leave.models import (
    HolidayRHCalendar as ModelHolidayRHCalendar,
)
from modules.leave.services.authz import require_admin_config

# -----------------------------------------------------------------------------
# Policy and Hierarchy Configuration
# -----------------------------------------------------------------------------


@transaction.atomic
def update_leave_policy(*, config_data: dict[str, Any]) -> LeavePolicyConfig:
    """Update current leave policy parameters. No draft/publish lifecycle; uses current values only."""
    require_admin_config(
        permission="leave.policy.update",
        actor=get_client().user_id,
    )

    # Validate and sanitize input based on current policy schema
    validated_data = {
        "cl_days": config_data.get("cl_days", 8),
        "rh_days": config_data.get("rh_days", 2),
        "scl_days": config_data.get("scl_days", 15),
        "el_days_staff": config_data.get("el_days_staff", 30),
        "vl_days_faculty": config_data.get("vl_days_faculty", 60),
        "col_days": config_data.get("col_days", 20),
    }

    # Ensure non-negative values
    for key, value in validated_data.items():
        if value < 0:
            raise ConflictError(f"{key} cannot be negative.")

    config = LeavePolicyConfig.objects.get_or_create(
        is_current=True,
        defaults={
            "cl_days": validated_data["cl_days"],
            "rh_days": validated_data["rh_days"],
            "scl_days": validated_data["scl_days"],
            "el_days_staff": validated_data["el_days_staff"],
            "vl_days_faculty": validated_data["vl_days_faculty"],
            "col_days": validated_data["col_days"],
        },
    )

    # Update existing record
    config[0].update(validated_data)
    config[0].save(
        update_fields=[
            "cl_days",
            "rh_days",
            "scl_days",
            "el_days_staff",
            "vl_days_faculty",
            "col_days",
        ]
    )

    return config[0]


@transaction.atomic
def update_hierarchy_config(*, config_data: dict[str, Any]) -> HierarchyConfig:
    """Update current hierarchy routing configuration."""
    require_admin_config(
        permission="leave.hierarchy.update",
        actor=get_client().user_id,
    )

    # Validate input structure against expected schema
    validated_data = {
        "unit_head_role": config_data.get("unit_head_role", "Unit Head"),
        "establishment_step_required": config_data.get("establishment_step_required", False),
        "director_self_sanction": config_data.get("director_self_sanction", True),
    }

    # Ensure boolean flags are valid
    if not isinstance(validated_data["establishment_step_required"], bool):
        raise ConflictError("establishment_step_required must be a boolean.")

    config = HierarchyConfig.objects.get_or_create(
        is_current=True,
        defaults={
            "unit_head_role": validated_data["unit_head_role"],
            "establishment_step_required": validated_data["establishment_step_required"],
            "director_self_sanction": validated_data["director_self_sanction"],
        },
    )

    # Update existing record
    config[0].update(validated_data)
    config[0].save(
        update_fields=["unit_head_role", "establishment_step_required", "director_self_sanction"]
    )

    return config[0]


# -----------------------------------------------------------------------------
# Holiday/RH Calendar Management
# -----------------------------------------------------------------------------


@transaction.atomic
def publish_holiday_calendar(*, calendar_data: dict[str, Any]) -> ModelHolidayRHCalendar:
    """Create or replace the currently effective published holiday/RH calendar."""
    require_admin_config(
        permission="leave.calendar.publish",
        actor=get_client().user_id,
    )

    # Validate date range and RH markers
    dates = calendar_data.get("dates", [])
    if not dates:
        raise ConflictError("At least one date entry is required.")

    for d in dates:
        if "date" not in d or "rh_marker" not in d:
            raise ConflictError("Each date entry must include 'date' and 'rh_marker'.")

    # Check for duplicate dates (enforce uniqueness)
    existing = ModelHolidayRHCalendar.objects.filter(
        date__year=dates[0]["date"].year,
        date__month=dates[0]["date"].month,
        date__day=dates[0]["date"].day,
    )
    if existing.exists():
        raise ConflictError("Duplicate date already exists in calendar.")

    # Create or update the published calendar
    calendar = ModelHolidayRHCalendar.objects.get_or_create(
        is_published=True,
        defaults={
            "dates": dates,
            "is_current": True,
        },
    )

    if calendar[0].exists():
        # Update existing published calendar
        calendar[0].update(dates)
        calendar[0].save(update_fields=["dates", "is_current"])
    else:
        # Create new published calendar
        calendar[0].save()

    return calendar[0]


# -----------------------------------------------------------------------------
# Offline Sanctioned Leave Records
# -----------------------------------------------------------------------------


@transaction.atomic
def record_offline_leave(
    *, employee_user_id: int, category: str, interval: dict[str, Any], sanction_ref: str
) -> Any | None:
    """Record an already-sanctioned offline leave to synchronize with the system."""
    require_admin_config(
        permission="leave.offline.record",
        actor=get_client().user_id,
    )

    # Validate inputs
    if not interval.get("start") or not interval.get("end"):
        raise ConflictError("Interval must include start and end dates.")

    # Determine account type based on category (simplified logic)
    account_type = "CL" if category == "CL" else "EL"

    # Create ledger entry for the offline sanction
    start_date = interval["start"]
    end_date = interval["end"]

    # Note: Actual implementation would involve complex balance calculations
    # based on BR-EL-011 (Continuous counting) and category rules.
    # This is a placeholder for the record creation logic.

    return None  # Placeholder for actual model interaction if LeaveSanctionRecord exists


# -----------------------------------------------------------------------------
# Authorized Leave Record Maintenance
# -----------------------------------------------------------------------------


@transaction.atomic
def maintain_leave_record(
    *, employee_user_id: int, action: str, details: dict[str, Any]
) -> Any | None:
    """Maintain authorized leave records (e.g., adjustments, corrections)."""
    require_admin_config(
        permission="leave.record.maintain",
        actor=get_client().user_id,
    )

    # Validate action type
    valid_actions = ["adjust_balance", "correct_period", "add_leave"]
    if action not in valid_actions:
        raise ConflictError(f"Invalid action. Must be one of: {valid_actions}")

    # Perform maintenance logic based on action and details
    # This would typically involve updating LeaveAccount or LeaveLedgerEntry models
    # ensuring consistency with current policy values from LeavePolicyConfig.

    return None  # Placeholder for actual model interaction


# -----------------------------------------------------------------------------
# SLA Threshold Configuration and Processing
# -----------------------------------------------------------------------------


@transaction.atomic
def configure_sla_thresholds(*, config_data: dict[str, Any]) -> Any | None:
    """Configure SLA thresholds for reminder and escalation."""
    require_admin_config(
        permission="leave.sla.configure",
        actor=get_client().user_id,
    )

    validated_data = {
        "reminder_threshold_hours": config_data.get("reminder_threshold_hours", 24),
        "escalation_threshold_hours": config_data.get("escalation_threshold_hours", 48),
        "escalation_action": config_data.get("escalation_action", "notify_supervisor"),
    }

    # Ensure positive thresholds
    if validated_data["reminder_threshold_hours"] <= 0:
        raise ConflictError("Reminder threshold must be positive.")
    if validated_data["escalation_threshold_hours"] <= 0:
        raise ConflictError("Escalation threshold must be positive.")

    # Store configuration (placeholder for SLAConfig model or similar)
    return None  # Placeholder for actual model interaction


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def get_current_policy() -> LeavePolicyConfig:
    """Retrieve the current leave policy configuration."""
    try:
        return LeavePolicyConfig.objects.get(is_current=True)
    except LeavePolicyConfig.DoesNotExist:
        raise NotFoundError("No current leave policy found.")


def get_current_hierarchy() -> HierarchyConfig:
    """Retrieve the current hierarchy configuration."""
    try:
        return HierarchyConfig.objects.get(is_current=True)
    except HierarchyConfig.DoesNotExist:
        raise NotFoundError("No current hierarchy configuration found.")


def get_effective_calendar() -> HolidayRHCalendar:
    """Retrieve the currently effective published holiday/RH calendar."""
    try:
        return ModelHolidayRHCalendar.objects.get(is_published=True, is_current=True)
    except ModelHolidayRHCalendar.DoesNotExist:
        raise NotFoundError("No effective holiday/RH calendar found.")
