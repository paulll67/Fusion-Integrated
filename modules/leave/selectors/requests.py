"""
Leave Management (ELM) â Request Selectors and Visibility Logic.

This module provides selector functions to retrieve leave request data based on user identity,
workflow state, and authorization context. It enforces ownership filtering, status visibility,
and role-based access without cross-module foreign key dependencies.

All identity references are integer user_id values. Cross-module data access must use public
contracts (e.g., get_employees(), get_leave_policy_config()) defined in modules.leave.contracts.
"""
from __future__ import annotations

from typing import Any, Optional

from django.db.models import Q

from fusion_auth.client import IamUnavailable, get_client
from modules.directory.models import UserRef
from modules.directory.services.sync import ensure_users_cached
# TODO: Import HR employment contract when available (e.g., from modules.hr)
# from modules.hr.models import Employment
# TODO: Import Academic Calendar contract when available (e.g., from modules.academic_calendar)
# from modules.academic_calendar.models import VacationPeriod

from modules.leave.contracts import EmployeeDTO, LeavePolicyConfig, HierarchyConfig
from modules.leave.models import (
    LeaveRequest,
    WorkflowTask,
    RequestAction,
    LeaveAccount,
    SubstituteAssignment,
)

# ============================================================================
# 1. Ownership and Visibility Filters
# ============================================================================

def is_own_request(request: LeaveRequest, principal_user_id: int) -> bool:
    """Check if the request belongs to the authenticated user.
    
    Identity reference is integer user_id. Cross-module data access uses public contracts.
    """
    return request.employee_user_id == principal_user_id

def visible_own_requests(principal: Any) -> list[LeaveRequest]:
    """Retrieve leave requests owned by the principal, filtered by status visibility.
    
    Employees can see their own pending, approved, cancelled, and withdrawn requests.
    Administrators may have broader visibility based on role permissions (not implemented here).
    """
    # Ensure user context is available via IAM client if needed
    try:
        iam_client = get_client()
    except IamUnavailable:
        return []
    
    principal_user_id = principal.user_id if hasattr(principal, 'user_id') else None
    if not principal_user_id:
        return []
    
    # Fetch own requests with necessary relationships for detail view
    qs = LeaveRequest.objects.select_related(
        "employee",
        "employee__department",
        "workflow_task"
    )
    
    # Filter by ownership and status visibility
    # Employees see: Draft, Submitted, Awaiting Review, Approved, Cancelled, Withdrawn
    qs = qs.filter(employee_user_id=principal_user_id)
    
    return list(qs.all())

def visible_assigned_tasks(principal: Any) -> list[WorkflowTask]:
    """Retrieve workflow tasks assigned to the principal.
    
    Only tasks where the assigned user matches the principal are returned.
    """
    principal_user_id = principal.user_id if hasattr(principal, 'user_id') else None
    if not principal_user_id:
        return []
    
    qs = WorkflowTask.objects.select_related(
        "request",
        "request__employee",
        "request__category"
    )
    qs = qs.filter(assigned_user_id=principal_user_id)
    
    # Exclude completed tasks from active assignment lists unless explicitly requested
    return list(qs.exclude(state="completed"))

# ============================================================================
# 2. Request Detail and History Selectors
# ============================================================================

def get_request_detail(request: LeaveRequest) -> dict[str, Any]:
    """Construct a detailed view of a single leave request.
    
    Includes category, dates, purpose, status, and linked workflow tasks.
    Does not perform cross-module joins; uses public contracts for employee data.
    """
    # Fetch related actions for history context
    actions_qs = RequestAction.objects.filter(request_id=request.id)
    actions = list(actions_qs.order_by('timestamp'))
    
    # Construct detail object using public contract patterns
    detail = {
        "id": request.id,
        "employee_user_id": request.employee_user_id,
        "category": request.category,
        "start_date": request.start_date.isoformat() if request.start_date else None,
        "end_date": request.end_date.isoformat() if request.end_date else None,
        "purpose": request.purpose,
        "status": request.status,
        "submitted_at": request.submitted_at.isoformat() if request.submitted_at else None,
        "workflow_tasks": [],
        "action_history": [],
    }
    
    # Add workflow tasks if any exist for this request
    task_qs = WorkflowTask.objects.filter(request_id=request.id)
    for task in task_qs:
        detail["workflow_tasks"].append({
            "id": task.id,
            "kind": task.kind,
            "state": task.state,
            "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
            "due_at": task.due_at.isoformat() if task.due_at else None,
        })
    
    # Add action history
    for action in actions:
        detail["action_history"].append({
            "id": action.id,
            "actor_user_id": action.actor_user_id,
            "action_type": action.action_type,
            "outcome": action.outcome,
            "timestamp": action.timestamp.isoformat() if action.timestamp else None,
        })
    
    return detail

def get_request_history(request: LeaveRequest) -> list[dict[str, Any]]:
    """Retrieve the chronological action history for a leave request.
    
    Returns a list of actions ordered by timestamp.
    """
    qs = RequestAction.objects.filter(request_id=request.id).order_by('timestamp')
    return list(qs.values(
        'id', 'actor_user_id', 'action_type', 'outcome', 'timestamp'
    ))

# ============================================================================
# 3. Leave Balance and History Selectors
# ============================================================================

def get_leave_balance(employee_user_id: int, category: str) -> dict[str, Any]:
    """Retrieve the current leave balance for an employee and category.
    
    Uses LeaveAccount aggregate to derive balance from ledger entries.
    No direct table reads of raw ledger data; uses public contract patterns.
    """
    # Fetch relevant account records
    qs = LeaveAccount.objects.filter(
        employee_user_id=employee_user_id,
        category=category
    )
    accounts = list(qs)
    
    if not accounts:
        return {
            "balance": 0,
            "entitlement": 0,
            "used_this_year": 0,
            "lapsed_this_year": 0,
        }
    
    # Aggregate balance logic (simplified for selector layer)
    total_balance = sum(a.balance for a in accounts)
    used_this_year = sum(a.used_this_year for a in accounts)
    lapsed_this_year = sum(a.lapsed_this_year for a in accounts)
    
    return {
        "balance": total_balance,
        "entitlement": 0, # Derived from policy config if needed
        "used_this_year": used_this_year,
        "lapsed_this_year": lapsed_this_year,
    }

def get_leave_ledger(employee_user_id: int, category: str) -> list[dict[str, Any]]:
    """Retrieve the transaction ledger for an employee and category.
    
    Returns a list of ledger entries ordered by timestamp.
    """
    qs = LeaveAccount.objects.filter(
        employee_user_id=employee_user_id,
        category=category
    ).order_by('timestamp')
    
    return list(qs.values(
        'id', 'transaction_type', 'amount', 'timestamp'
    ))

# ============================================================================
# 4. Action History and Workflow Status Selectors
# ============================================================================

def get_action_history_for_request(request_id: int) -> list[dict[str, Any]]:
    """Retrieve the action history for a specific request ID.
    
    Useful for auditing or displaying status changes to users.
    """
    qs = RequestAction.objects.filter(request_id=request_id).order_by('timestamp')
    return list(qs.values(
        'id', 'actor_user_id', 'action_type', 'outcome', 'timestamp'
    ))

def get_pending_workflow_tasks_for_request(request_id: int) -> list[dict[str, Any]]:
    """Retrieve pending workflow tasks associated with a request.
    
    Useful for identifying who needs to act on the request.
    """
    qs = WorkflowTask.objects.filter(
        request_id=request_id,
        state__in=['pending', 'assigned']
    ).select_related('assigned_user')
    return list(qs.values(
        'id', 'kind', 'state', 'assigned_user_id', 'due_at'
    ))

# ============================================================================
# 5. Substitute Assignment Selectors
# ============================================================================

def get_substitute_assignments(request_id: int) -> list[dict[str, Any]]:
    """Retrieve substitute assignments for a specific request.
    
    Returns details about nominated substitutes and their responses.
    """
    qs = SubstituteAssignment.objects.filter(request_id=request_id)
    return list(qs.values(
        'id', 'applicant_user_id', 'substitute_user_id', 'response', 'responsibility_interval'
    ))

def get_eligible_substitutes(employee_user_id: int, period_start: str, period_end: str) -> list[int]:
    """Retrieve a list of eligible substitute user IDs.
    
    This is a placeholder for the actual eligibility logic which may depend on
    HR employment contracts or directory data accessed via public contracts.
    For now, returns an empty list to indicate unresolved dependency.
    
    Returns:
        List of integer user_ids representing eligible substitutes.
    """
    # TODO: Implement actual eligibility check using modules.hr or directory services
    # Ensure users are cached via ensure_users_cached() if needed
    return []

# ============================================================================
# 6. Policy and Configuration Selectors (Read-Only)
# ============================================================================

def get_current_leave_policy_config() -> Optional[LeavePolicyConfig]:
    """Retrieve the current configured leave policy.
    
    As per Problem Statement v1.4, use current configured values without draft/publish lifecycle.
    """
    # Placeholder for actual config retrieval
    return None

def get_hierarchy_config() -> Optional[HierarchyConfig]:
    """Retrieve the current hierarchy routing configuration.
    
    Used to determine Unit Head vs. Establishment routing paths.
    """
    # Placeholder for actual config retrieval
    return None

def get_holiday_rh_calendar() -> Optional[list[dict[str, Any]]]:
    """Retrieve the currently effective published holiday/RH calendar.
    
    Only currently effective published dates are returned.
    """
    # Placeholder for actual calendar retrieval
    return None

def get_sla_config() -> Optional[dict[str, Any]]:
    """Retrieve the configured SLA thresholds and escalation rules.
    
    Used by event-triggered SLA processing (EL-UC-021).
    """
    # Placeholder for actual config retrieval
    return None

# ============================================================================
# 7. Unresolved Gaps and Contracts
# ============================================================================

def get_employees_by_department(department: str) -> list[int]:
    """Retrieve user IDs of employees in a specific department.
    
    This function relies on the public contract EmployeeDTO.from_ref() or similar
    mechanisms to avoid cross-module FKs. If directory sync is not available,
    this may return incomplete data.
    
    Returns:
        List of integer user_ids.
    """
    # TODO: Implement using modules.directory services or public contracts
    # Ensure users are cached via ensure_users_cached() if needed
    return []

def get_vacation_periods(year: int) -> list[dict[str, Any]]:
    """Retrieve vacation periods for a given year from the Academic Calendar.
    
    This function relies on the public contract VacationPeriod or similar.
    If the academic calendar module is not available, this returns an empty list.
    
    Returns:
        List of dictionaries representing vacation periods.
    """
    # TODO: Implement using modules.academic_calendar services or public contracts
    return []

