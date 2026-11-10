"""Registered Leave models.

The generated aggregate files contain overlapping model declarations.  The
accounts aggregate is the single registered surface used by the module package
so Django does not register duplicate model names during app loading.
"""

from modules.leave.models.accounts import (
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
    VacationPeriodConfig,
    WorkflowTask,
)

__all__ = [
    "HierarchyConfig",
    "HolidayRHCalendar",
    "LeaveAccount",
    "LeaveLedgerEntry",
    "LeavePolicyConfig",
    "LeaveRequest",
    "OfflineSanctionRecord",
    "RequestAction",
    "ResumptionRecord",
    "SLAConfig",
    "SubstituteAssignment",
    "VacationPeriodConfig",
    "WorkflowTask",
]
