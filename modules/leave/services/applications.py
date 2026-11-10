"""
Employee Leave Management (ELM) — Application Command Services.

Implements command handlers for leave lifecycle operations: submission, withdrawal, cancellation, extension, resumption, and substitute management.

Adheres to Workflow v1.6 state transitions and Problem Statement v1.4 policy semantics.
Uses current configured policy values without draft/publish/effective-version lifecycles.
Identity references are integer user_id values; cross-module data uses public contracts.
"""

from __future__ import annotations

import logging

from django.utils import timezone

from core.api.exceptions import DomainError
from modules.placement.domain import state_machine as sm
from modules.placement.models import (
    Application,
    ApplicationTransition,
    HolidayRHCalendar,
)
from modules.placement.services import notifications

log = logging.getLogger("fusion.leave.applications")

# -- Constants --
VALID_CATEGORIES = ["CL", "RH", "SCL", "EL", "COL", "VL"]
ALLOWED_SUBSTITUTE_ACTIONS = ["ACCEPT", "DECLINE"]


def _validate_request_data(data: dict) -> None:
    """Validate transport layer constraints for a new leave request.

    Raises DomainError if validation fails. Business rules (balance, overlap) are checked in services.
    """
    category = data.get("category")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    purpose = data.get("purpose", "")
    station_details = data.get("station_leave_details")
    substitute_user_id = data.get("substitute_user_id")

    if not category or category not in VALID_CATEGORIES:
        raise DomainError(f"Invalid leave category: {category}", code="invalid_category")

    if start_date and end_date and start_date > end_date:
        raise DomainError("Start date must be before or equal to end date", code="invalid_dates")

    if purpose and not isinstance(purpose, str):
        raise DomainError("Purpose must be a string", code="invalid_purpose")

    # Station Leave details are optional JSON; validate structure if present
    if station_details:
        if not isinstance(station_details, dict):
            raise DomainError(
                "Station leave details must be a dictionary", code="invalid_station_details"
            )

    # Substitute validation is handled by domain service to check eligibility and overlap
    if substitute_user_id:
        if not isinstance(substitute_user_id, int) or substitute_user_id <= 0:
            raise DomainError(
                "Substitute user ID must be a positive integer", code="invalid_substitute_id"
            )

    # Ensure employee is not submitting for themselves in substitute context (handled by domain)
    if substitute_user_id and data.get("employee_user_id") == substitute_user_id:
        raise DomainError("Substitute cannot be the applicant", code="invalid_substitute_self")


def _get_current_policy() -> dict:
    """Retrieve current configured leave policy parameters.

    Per PS v1.4, no draft/publish/effective-version lifecycle is used; only current values apply.
    """
    # Placeholder for actual policy retrieval logic (e.g., from config service or DB)
    # In a real implementation, this would fetch active configuration values.
    return {
        "cl_days": 8,
        "rh_days": 2,
        "scl_days": 15,
        "el_days": 30,
        "vl_days": 60,
        "col_days": 20,
    }


def _get_current_calendar() -> HolidayRHCalendar:
    """Retrieve the currently effective published holiday/RH calendar.

    Per PS v1.4 and BR-EL-031, only the currently effective published calendar is used.
    """
    # Placeholder for actual calendar retrieval logic (e.g., from service or DB)
    return HolidayRHCalendar.objects.filter(published=True).first()


def _get_hierarchy_config(employee_user_id: int) -> dict:
    """Retrieve current hierarchy configuration for an employee.

    Includes routing facts and optional Establishment step.
    """
    # Placeholder for actual hierarchy retrieval logic (e.g., from config service or DB)
    return {
        "unit_head_id": 1,
        "sanctioning_authority_ids": [2, 3],
        "has_establishment_step": False,
    }


def _check_balance_and_eligibility(employee_user_id: int, category: str) -> bool:
    """Check if the employee has sufficient leave balance for the requested category.

    This is a simplified check; actual balance logic resides in LeaveAccount/LeaveLedgerEntry services.
    """
    # Placeholder for actual balance check logic (e.g., from domain service)
    return True


def _check_overlap(employee_user_id: int, start_date: str, end_date: str) -> bool:
    """Check if the requested period overlaps with active or approved leave.

    First-half and second-half CL on the same date are not treated as overlapping (BR-EL-012).
    """
    # Placeholder for actual overlap check logic (e.g., from domain service)
    return False


def _check_substitute_eligibility(substitute_user_id: int, start_date: str, end_date: str) -> bool:
    """Check if the nominated substitute is eligible and has no overlapping leave.

    Per BR-EL-014 and BR-EL-015.
    """
    # Placeholder for actual substitute eligibility check logic (e.g., from domain service)
    return True


def _create_leave_request(data: dict, employee_user_id: int) -> Application:
    """Create a new leave request application.

    Validates data at transport layer and checks balance/overlap in services.
    """
    # Validate transport layer
    _validate_request_data(data)

    # Check business rules (balance, overlap, substitute eligibility)
    if not _check_balance_and_eligibility(employee_user_id, data.get("category")):
        raise DomainError("Insufficient leave balance", code="insufficient_balance")

    start_date = data.get("start_date")
    end_date = data.get("end_date")
    if not _check_overlap(employee_user_id, start_date, end_date):
        raise DomainError("Leave period overlaps with existing leave", code="overlap_detected")

    # Check substitute eligibility if required
    substitute_user_id = data.get("substitute_user_id")
    if substitute_user_id and not _check_substitute_eligibility(
        substitute_user_id, start_date, end_date
    ):
        raise DomainError(
            "Substitute is not eligible or has overlapping leave", code="invalid_substitute"
        )

    # Create the application instance
    application = Application.objects.create(
        user_id=employee_user_id,
        category=data.get("category"),
        start_date=start_date,
        end_date=end_date,
        purpose=data.get("purpose", ""),
        station_leave_details=data.get("station_leave_details"),
        submitted_at=timezone.now(),
    )

    # Determine next state based on category and substitute requirement
    category = data.get("category")
    has_substitute = bool(data.get("substitute_user_id"))
    is_director = employee_user_id == 100  # Placeholder for Director ID check

    if category in ["CL", "RH"]:
        if has_substitute and not is_director:
            application.state = sm.STATE_AWAITING_SUBSTITUTE_RESPONSE
        else:
            application.state = sm.STATE_AWAITING_UNIT_HEAD_REVIEW
    elif category in ["SCL", "EL", "COL", "VL"]:
        # Higher sanction path for these categories (per PS v1.4)
        if has_substitute and not is_director:
            application.state = sm.STATE_AWAITING_SUBSTITUTE_RESPONSE
        else:
            application.state = (
                sm.STATE_AWAITING_UNIT_HEAD_REVIEW
            )  # Unit Head reviews first, then higher authority
    elif category == "VL":
        # VL requires vacation period check (per PS v1.4)
        calendar = _get_current_calendar()
        if not calendar:
            raise DomainError("No valid holiday/RH calendar found", code="calendar_not_found")

        start_date = data.get("start_date")
        end_date = data.get("end_date")
        # Placeholder for vacation period validation logic
        if not _is_valid_vacation_period(start_date, end_date, calendar):
            raise DomainError(
                "Vacation leave must be within a valid vacation period",
                code="invalid_vacation_period",
            )

        application.state = sm.STATE_AWAITING_UNIT_HEAD_REVIEW
    else:
        raise DomainError(f"Unsupported leave category: {category}", code="unsupported_category")

    # Save the state change (transition)
    ApplicationTransition.objects.create(
        application=application,
        from_state=sm.STATE_DRAFT,
        to_state=application.state,
        actor_kind=sm.EMPLOYEE,
        use_case_id="EL-UC-001",
    )

    return application


def _is_valid_vacation_period(start_date: str, end_date: str, calendar: HolidayRHCalendar) -> bool:
    """Check if the requested period falls within a valid vacation period.

    Per PS v1.4 and BR-EL-006.
    """
    # Placeholder for actual vacation period validation logic (e.g., from domain service)
    return True


def _process_substitute_response(application: Application, user_id: int, action: str) -> None:
    """Process a substitute's response to a leave request.

    Accepts or declines the assignment. If declined, allows replacement nomination (UC-019).
    """
    if action not in ALLOWED_SUBSTITUTE_ACTIONS:
        raise DomainError(f"Invalid substitute action: {action}", code="invalid_substitute_action")

    # Update application state based on response
    if action == "ACCEPT":
        application.state = sm.STATE_AWAITING_UNIT_HEAD_REVIEW
    else:  # DECLINE
        application.state = sm.STATE_APPlicant_ACTION_REQUIRED

    ApplicationTransition.objects.create(
        application=application,
        from_state=sm.STATE_AWAITING_SUBSTITUTE_RESPONSE,
        to_state=application.state,
        actor_kind=sm.SUBSTITUTE,
        use_case_id="EL-UC-002",
    )

    # Notify applicant if action required (decline)
    if action == "DECLINE":
        notifications.send_notification(
            recipient_id=application.user_id,
            message="Substitute declined your request. You may nominate a replacement or withdraw.",
        )


def _process_withdrawal(application: Application, user_id: int) -> None:
    """Process a withdrawal of a pending leave request.

    Per PS v1.4 and BR-EL-022, pending requests can be withdrawn before final approval.
    """
    # Check if application is still pending (not yet approved/rejected)
    if application.state in [sm.STATE_APPROVED, sm.STATE_REJECTED]:
        raise DomainError(
            "Cannot withdraw an already finalized request", code="withdrawal_after_finalization"
        )

    # Update state to withdrawn
    application.state = sm.STATE_WITHDRAWN
    ApplicationTransition.objects.create(
        application=application,
        from_state=application.state,
        to_state=sm.STATE_WITHDRAWN,
        actor_kind=sm.EMPLOYEE,
        use_case_id="EL-UC-007",
    )

    # Notify relevant roles (e.g., Unit Head)
    notifications.send_notification(
        recipient_id=application.unit_head_id,
        message="Leave request withdrawn by employee.",
    )


def _process_cancellation(application: Application, user_id: int) -> None:
    """Process a cancellation of an approved leave request.

    Per PS v1.4 and BR-EL-023, cancellation is allowed before the approved leave begins.
    Follows applicable hierarchy for decision.
    """
    # Check if application is approved but not yet started (placeholder logic)
    if application.state != sm.STATE_APPROVED:
        raise DomainError("Can only cancel an approved leave", code="not_approved")

    # Determine hierarchy path for cancellation (similar to original approval)
    # Placeholder: Direct to Unit Head or higher authority based on config
    next_state = sm.STATE_AWAITING_UNIT_HEAD_REVIEW  # Placeholder for actual routing logic

    application.state = next_state
    ApplicationTransition.objects.create(
        application=application,
        from_state=sm.STATE_APPROVED,
        to_state=next_state,
        actor_kind=sm.EMPLOYEE,
        use_case_id="EL-UC-008",
    )

    # Notify Unit Head or higher authority
    notifications.send_notification(
        recipient_id=application.unit_head_id,
        message="Employee requested cancellation of approved leave.",
    )


def _process_extension(application: Application, user_id: int, extension_data: dict) -> None:
    """Process an extension of an ongoing leave request.

    Per PS v1.4 and BR-EL-025, applicable for EL/COL/VL. Requires review/routing as per hierarchy.
    """
    # Check if application is in a state allowing extension (e.g., approved but ongoing)
    if application.state not in [sm.STATE_APPROVED]:
        raise DomainError("Can only extend an approved leave", code="not_approved")

    # Placeholder for actual extension logic (balance adjustment, period sync)
    # This would involve updating LeaveLedgerEntry and potentially creating a new Application or modifying existing

    # Determine next state based on hierarchy config
    next_state = sm.STATE_AWAITING_UNIT_HEAD_REVIEW  # Placeholder for actual routing logic

    application.state = next_state
    ApplicationTransition.objects.create(
        application=application,
        from_state=sm.STATE_APPROVED,
        to_state=next_state,
        actor_kind=sm.EMPLOYEE,
        use_case_id="EL-UC-009",
    )

    # Notify Unit Head or higher authority
    notifications.send_notification(
        recipient_id=application.unit_head_id,
        message="Employee requested extension of approved leave.",
    )


def _process_resumption(application: Application, user_id: int, resumption_data: dict) -> None:
    """Process a resumption of duty submission.

    Per PS v1.4 and BR-EL-027, applicable for EL/COL/VL. Requires review by authority.
    """
    # Check if application is in a state allowing resumption (e.g., approved but not returned)
    if application.state not in [sm.STATE_APPROVED]:
        raise DomainError("Can only submit resumption for an approved leave", code="not_approved")

    # Placeholder for actual resumption logic (balance sync, period adjustment)
    # This would involve updating LeaveLedgerEntry and potentially creating a ResumptionRecord

    # Determine next state based on review outcome (placeholder: awaiting review)
    next_state = sm.STATE_AWAITING_RESUMPTION_REVIEW  # Placeholder for actual routing logic

    application.state = next_state
    ApplicationTransition.objects.create(
        application=application,
        from_state=sm.STATE_APPROVED,
        to_state=next_state,
        actor_kind=sm.EMPLOYEE,
        use_case_id="EL-UC-010",
    )

    # Notify authority
    notifications.send_notification(
        recipient_id=application.unit_head_id,
        message="Employee submitted resumption of duty.",
    )


def _process_resumption_review(application: Application, user_id: int, review_data: dict) -> None:
    """Process a resumption review by the applicable authority.

    Per PS v1.4 and BR-EL-028, determines normal/early/late outcome and syncs balance/period.
    """
    # Placeholder for actual review logic (compare actual return date with approved period)
    # This would involve updating LeaveLedgerEntry based on early/late/normal findings

    # Determine next state based on review outcome (e.g., reviewed and closed)
    next_state = sm.STATE_RESUMPTION_REVIEWED  # Placeholder for actual routing logic

    application.state = next_state
    ApplicationTransition.objects.create(
        application=application,
        from_state=sm.STATE_AWAITING_RESUMPTION_REVIEW,
        to_state=next_state,
        actor_kind=sm.SANCTIONING_AUTHORITY,
        use_case_id="EL-UC-011",
    )

    # Notify employee of outcome
    notifications.send_notification(
        recipient_id=application.user_id,
        message="Resumption review completed.",
    )


def _process_year_end(application: Application) -> None:
    """Process year-end leave balance processing.

    Per PS v1.4 and BR-EL-028, handles lapse of CL/RH/SCL, carry-forward of EL/COL, VL-to-EL conversion.
    Event-triggered, not actor-triggered.
    """
    # Placeholder for actual year-end logic (ledger updates, balance adjustments)
    # This would involve querying LeaveLedgerEntry and applying rules from BR-EL-002 to BR-EL-008

    log.info("Year-end processing triggered for leave balances.")


def _process_sla_threshold(application: Application) -> None:
    """Process SLA threshold event for pending tasks.

    Per PS v1.4 and BR-EL-032/033, sends reminder or escalates routing if task remains pending.
    Event-triggered, not actor-triggered.
    """
    # Placeholder for actual SLA logic (check due date, send notification, potentially escalate)

    log.info("SLA threshold reached for application.")
    notifications.send_notification(
        recipient_id=application.unit_head_id,
        message="SLA reminder: Leave request pending.",
    )
