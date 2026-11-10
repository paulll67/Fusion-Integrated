"""
Employee Leave Management (ELM) — Services Package Exports.

The services in this package implement domain logic, workflow orchestration, and
state management for leave applications, balances, policies, and notifications.
All identity references are integer user_id values. Cross-module data access
must use public contracts defined in modules.leave.contracts.
"""
from __future__ import annotations

from typing import Any

# Core Domain Services
from modules.leave.services.leaves import LeaveService, LeaveAccountService
from modules.leave.services.workflows import WorkflowService
from modules.leave.services.policies import PolicyService
from modules.leave.services.hierarchy import HierarchyService
from modules.leave.services.calendar import CalendarService
from modules.leave.services.substitute import SubstituteService
from modules.leave.services.sla import SLAService

# Public API Exports (for external module consumption)
from modules.leave.contracts import EmployeeDTO, LeaveRequestDTO, WorkflowTaskDTO

__all__ = [
    # Core Services
    "LeaveService",
    "LeaveAccountService",
    "WorkflowService",
    "PolicyService",
    "HierarchyService",
    "CalendarService",
    "SubstituteService",
    "SLAService",
    # DTOs for external consumption
    "EmployeeDTO",
    "LeaveRequestDTO",
    "WorkflowTaskDTO",
]
