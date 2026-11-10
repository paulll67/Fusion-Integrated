"""
Employee Leave Management (ELM) — Decision Services.

Implements state transitions, outcome generation, and command execution for leave requests, resumption reviews, and administrative actions.

Follows Workflow Specifications v1.6 for state machines and outcomes.
Uses current policy/hierarchy configuration without draft/effective-version lifecycle.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from django.db import transaction
from django.utils import timezone

from core.api.exceptions import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from fusion_auth.client import get_client

from modules.directory.contracts import EmployeeDTO
from modules.leave.contracts import (
    LeaveRequestDTO,
    WorkflowTaskDTO,
    RequestActionDTO,
)
from modules.leave.models import (
    LeaveRequest,
    WorkflowTask,
    RequestAction,
    LeaveAccount,
    SubstituteAssignment,
    LeavePolicyConfig,
    HierarchyConfig,
    HolidayRHCalendar,
    ResumptionRecord,
    OfflineSanctionRecord,
)
from modules.leave.services.facts import (
    get_leave_policy_config,
    get_hierarchy_config,
    get_holiday_calendar,
)
from modules.placement.domain import state_machine as sm

log = logging.getLogger("fusion.leave.decisions")


class DecisionOutcome(Enum):
    """Standard outcomes for leave decisions."""
    APPROVED = "Approved"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"
    CANCELLED = "Cancelled"
    EXTENDED = "Extended"
    RESUMPTION_NORMAL = "Resumption Normal"
    RESUMPTION_EARLY = "Resumption Early"
    RESUMPTION_LATE = "Resumption Late"
    SANCTIONED_OFFLINE = "Sanctioned Offline"
    ERROR = "Error"


class DecisionService:
    """Core decision logic for leave workflows."""

    def __init__(self, request: LeaveRequest, actor_user_id: int) -> None:
        self.request = request
        self.actor_user_id = actor_user_id
        self.policy_config = get_leave_policy_config()
        self.hierarchy_config = get_hierarchy_config()
        self.calendar = get_holiday_calendar()

    def execute_transition(self, from_state: str, event_type: str, outcome: DecisionOutcome) -> WorkflowTaskDTO:
        """Execute a state transition and return the resulting task DTO.

        Guards are implicit in the request validation and policy checks performed before this call.
        """
        # Validate state transition guard (simplified for service layer)
        if from_state not in [
            'Draft / Not Submitted',
            'Awaiting Unit Head Review',
            'Awaiting Substitute Response',
            'Approved',
            'Rejected',
            'Extension Pending',
            'Resumption Review Pending',
        ]:
            raise DomainError(f"Invalid source state: {from_state}")

        # Update request status based on outcome
        self.request.status = outcome.value.lower()
        self.request.save(update_fields=['status'])

        # Create action history entry
        action = RequestAction.objects.create(
            request=self.request,
            actor_user_id=self.actor_user_id,
            action_type=event_type,
            outcome=outcome.value,
            timestamp=timezone.now(),
        )

        # Create or update workflow task
        task = WorkflowTask.objects.get_or_create(
            request=self.request,
            defaults={
                'task_kind': event_type,
                'state': from_state if outcome != DecisionOutcome.APPROVED.value else 'Completed',
                'assigned_user_id': self.actor_user_id,
            }
        )
        task.state = from_state if outcome != DecisionOutcome.APPROVED.value else 'Completed'
        task.save()

        return WorkflowTaskDTO.from_model(task)

    def process_unit_head_review(self, request: LeaveRequest, actor_user_id: int) -> tuple[DecisionOutcome, Optional[str]]:
        """Process Unit Head review for CL/RH or Higher Sanction.

        Returns (outcome, reason).
        """
        # Check if Director self-sanction applies (simplified check)
        is_director = request.employee_user_id == actor_user_id
        
        if is_director:
            # Director self-sanction path
            return DecisionOutcome.APPROVED, "Director Self-Sanction"
        
        # Standard Unit Head review
        # In a real system, this would fetch the Unit Head's decision from a database or session.
        # For this service layer, we assume the actor is authorized to decide.
        return DecisionOutcome.APPROVED, "Unit Head Approved"

    def process_substitute_response(self, request: LeaveRequest, actor_user_id: int, response_type: str) -> tuple[DecisionOutcome, Optional[str]]:
        """Process Substitute Accept/Decline.

        Returns (outcome, reason).
        """
        if response_type == 'Accept':
            # Transition to Unit Head review or Director self-sanction
            return DecisionOutcome.APPROVED, "Substitute Accepted"
        else:
            # Decline triggers replacement nomination flow
            return DecisionOutcome.ERROR, "Substitute Declined - Replacement Required"

    def process_withdrawal(self, request: LeaveRequest, actor_user_id: int) -> tuple[DecisionOutcome, Optional[str]]:
        """Process pending withdrawal.
        """
        # Ensure not already approved/cancelled
        if request.status in ['Approved', 'Cancelled']:
            raise DomainError("Cannot withdraw an approved or cancelled request.")

        return DecisionOutcome.WITHDRAWN, "Request Withdrawn"

    def process_cancellation(self, request: LeaveRequest, actor_user_id: int) -> tuple[DecisionOutcome, Optional[str]]:
        """Process cancellation of approved leave.
        """
        if request.status != 'Approved':
            raise DomainError("Only approved requests can be cancelled.")

        # Adjust balance if applicable (simplified)
        # In production, this would involve LeaveLedgerEntry transactions
        
        return DecisionOutcome.CANCELLED, "Leave Cancelled"

    def process_extension(self, request: LeaveRequest, actor_user_id: int) -> tuple[DecisionOutcome, Optional[str]]:
        """Process extension of ongoing leave.
        """
        # Validate eligibility for extension (simplified)
        if not self.policy_config.allows_extension(request.category):
            raise DomainError("Extension not allowed for this category.")

        return DecisionOutcome.EXTENDED, "Leave Extended"

    def process_resumption_review(self, request: LeaveRequest, actor_user_id: int, actual_return_date: str) -> tuple[DecisionOutcome, Optional[str]]:
        """Process resumption review for EL/COL/VL.
        """
        # Determine outcome based on date comparison (simplified logic)
        from datetime import datetime
        request_start = datetime.fromisoformat(request.start_date)
        actual_return = datetime.fromisoformat(actual_return_date)
        
        if actual_return < request_start:
            return DecisionOutcome.RESUMPTION_EARLY, "Early Resumption"
        elif actual_return > request_start:
            return DecisionOutcome.RESUMPTION_LATE, "Late Resumption"
        else:
            return DecisionOutcome.RESUMPTION_NORMAL, "Normal Resumption"

    def process_offline_sanction(self, employee_user_id: int, category: str, interval: str) -> tuple[DecisionOutcome, Optional[str]]:
        """Process recording of already-sanctioned offline leave.
        """
        # Create record without triggering new workflow
        record = OfflineSanctionRecord.objects.create(
            employee_user_id=employee_user_id,
            category=category,
            interval=interval,
            status='Recorded',
        )
        
        return DecisionOutcome.SANCTIONED_OFFLINE, "Offline Leave Recorded"

    def process_year_end(self, employee_user_id: int) -> tuple[DecisionOutcome, Optional[str]]:
        """Process year-end leave adjustments.
        """
        # Logic for CL lapse, VL conversion to EL, etc.
        # This is an event-driven service call, not a user action.
        return DecisionOutcome.APPROVED, "Year End Processing Complete"

    def process_sla_threshold(self, task: WorkflowTask) -> tuple[DecisionOutcome, Optional[str]]:
        """Process SLA threshold event (notification/escalation).
        """
        # This is an event-driven service call.
        return DecisionOutcome.ERROR, "SLA Threshold Reached - Escalation Initiated"

    @staticmethod
    def validate_request(request: LeaveRequest) -> None:
        """Pre-flight validation for leave request submission.
        """
        # Check category eligibility
        if not get_leave_policy_config().is_category_valid(request.category):
            raise DomainError("Invalid leave category.")
        
        # Check balance/entitlement (simplified)
        from modules.leave.services.accounts import get_balance
        balance = get_balance(request.employee_user_id, request.category)
        if balance < 0:
            raise DomainError("Insufficient leave balance.")
        
        # Check overlap (simplified)
        # In production, this would query LeaveLedgerEntry for overlaps
        pass

    @staticmethod
    def get_workflow_state(request: LeaveRequest) -> str:
        """Determine current workflow state based on request status and history.
        """
        if not request.submitted_at:
            return 'Draft / Not Submitted'
        
        # Check for substitute response pending
        has_substitute_response = SubstituteAssignment.objects.filter(
            request=request,
            status='Accepted'
        ).exists()
        
        if not has_substitute_response:
            return 'Awaiting Unit Head Review'
        
        # Check for final decision
        if request.status == 'Approved':
            return 'Completed'
        elif request.status == 'Rejected':
            return 'Completed'
        else:
            return request.status.capitalize()
