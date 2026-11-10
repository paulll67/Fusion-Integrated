"""What the server tells the shell about this module (ADR-0011).

Nav items carry `required_permission` and the server filters before sending —
the client does zero filtering, so a link a role cannot use never reaches the
browser at all.
"""

from typing import Any

MODULE = {
    "code": "leave",
    "label": "Leave",
    "icon": "calendar-check",
    "base_path": "/leave",
    "nav_section": "Employee Services",
    "sort_order": 15,
    "status": "active",
}

NAV_ITEMS = [
    # -- Employee Self-Service (Primary View) --------------------------------
    {"code": "leave.mine", "label": "My Leave Requests",
     "icon": "UserCheck", "to": "/leave/mine",
     "required_permission": "leave.request.view_self",
     "sort_order": 5},
    {"code": "leave.balances", "label": "Leave Balances",
     "icon": "CalendarAlt", "to": "/leave/balances",
     "required_permission": "leave.balance.view",
     "sort_order": 10},
    {"code": "leave.history", "label": "Leave History",
     "icon": "History", "to": "/leave/history",
     "required_permission": "leave.request.view_self",
     "sort_order": 15},
    {"code": "leave.export", "label": "Export Application",
     "icon": "Download", "to": "/leave/export",
     "required_permission": "leave.application.export",
     "sort_order": 20},

    # -- Employee Actions (Conditional on State/Role) -------------------------
    {"code": "leave.create", "label": "Apply for Leave",
     "icon": "PlusCircle", "to": "/leave/create",
     "required_permission": "leave.request.create",
     "sort_order": 25},
    {"code": "leave.withdraw", "label": "Withdraw Request",
     "icon": "TrashAlt", "to": "/leave/withdraw",
     "required_permission": "leave.request.revoke",
     "sort_order": 30},
    {"code": "leave.cancellation", "label": "Cancel Approved Leave",
     "icon": "Ban", "to": "/leave/cancellation",
     "required_permission": "leave.request.revoke",
     "sort_order": 35},
    {"code": "leave.extension", "label": "Extend Ongoing Leave",
     "icon": "Clock", "to": "/leave/extension",
     "required_permission": "leave.request.create",
     "sort_order": 40},
    {"code": "leave.resumption", "label": "Submit Resumption",
     "icon": "CheckCircle", "to": "/leave/resumption",
     "required_permission": "leave.resumption.create",
     "sort_order": 45},

    # -- Admin & Management (Restricted) --------------------------------------
    {"code": "leave.tasks", "label": "My Tasks",
     "icon": "Tasks", "to": "/leave/tasks",
     "required_permission": "leave.workflow_task.view",
     "sort_order": 50},
    {"code": "leave.substitute", "label": "Respond to Substitute",
     "icon": "UserPlus", "to": "/leave/substitute",
     "required_permission": "leave.workflow_task.update",
     "sort_order": 55},

    # -- Administration (Authorized Roles Only) -------------------------------
    {"code": "leave.admin.policy", "label": "Policy Configuration",
     "icon": "Cog", "to": "/admin/policy",
     "required_permission": "leave.policy.manage",
     "sort_order": 60},
    {"code": "leave.admin.hierarchy", "label": "Hierarchy Routing",
     "icon": "Tree", "to": "/admin/hierarchy",
     "required_permission": "leave.hierarchy.manage",
     "sort_order": 65},
    {"code": "leave.admin.calendar", "label": "Holiday/RH Calendar",
     "icon": "CalendarAlt", "to": "/admin/calendar",
     "required_permission": "leave.calendar.manage",
     "sort_order": 70},
    {"code": "leave.admin.sla", "label": "SLA Thresholds",
     "icon": "Bell", "to": "/admin/sla",
     "required_permission": "leave.sla.manage",
     "sort_order": 75},
    {"code": "leave.admin.records", "label": "Leave Records Maintenance",
     "icon": "FileText", "to": "/admin/records",
     "required_permission": "leave.record.manage",
     "sort_order": 80},
]

#: Every permission this module recognises; ROLE_GRANTS below says who holds each.
PERMISSIONS = [
    # -- Employee Leave Lifecycle ---------------------------------------------
    ("leave.request.view", "View leave requests within scope"),
    ("leave.request.view_self", "View own leave requests"),
    ("leave.request.create", "Create a new leave application"),
    ("leave.request.review", "Review leave applications (Unit Head/Authority)"),
    ("leave.request.approve", "Approve leave applications"),
    ("leave.request.assign", "Assign tasks to users"),
    ("leave.request.revoke", "Withdraw or cancel pending/approved requests"),
    ("leave.request.export", "Export printable application"),

    # -- Workflow & Tasks -----------------------------------------------------
    ("leave.workflow_task.view", "View assigned workflow tasks"),
    ("leave.workflow_task.update", "Update task status/assignment"),
    ("leave.workflow_task.assign", "Assign a task to another user"),

    # -- Balances & History --------------------------------------------------
    ("leave.balance.view", "View leave balances"),
    ("leave.request.view_self", "View own request history"),

    # -- Administration & Configuration --------------------------------------
    ("leave.policy.manage", "Manage leave policy configuration"),
    ("leave.hierarchy.manage", "Manage routing hierarchy configuration"),
    ("leave.calendar.manage", "Manage holiday/RH calendar data"),
    ("leave.calendar.publish", "Publish holiday/RH calendar"),
    ("leave.record.manage", "Maintain authorized leave records"),
    ("leave.sla.manage", "Configure SLA thresholds"),
    ("leave.account.update", "Update leave account balances"),
]

#: Performed by a service or a scheduled task, so no designation holds them.
SYSTEM_PERMISSIONS = [
    "leave.workflow_task.assign",
    "leave.account.update",
]

#: Role definitions derived from ELM actor roles (Unit Head, Director, Admin).
# Note: Exact IAM strings must match the fixture; these are placeholders for the blueprint.
_STUDENT_EMPLOYEE = [
    "leave.request.view_self",
    "leave.request.create",
    "leave.request.revoke",
    "leave.balance.view",
    "leave.history.view",
    "leave.application.export",
    "leave.resumption.create",
]

_UNIT_HEAD = [
    "leave.request.view",
    "leave.request.review",
    "leave.workflow_task.view",
    "leave.workflow_task.assign",
    "leave.balance.view",
]

_SANCTIONING_AUTHORITY = [
    "leave.request.approve",
    "leave.request.review",
    "leave.workflow_task.view",
    "leave.account.update",
]

_LEAVE_ADMINISTRATOR = [
    "leave.policy.manage",
    "leave.hierarchy.manage",
    "leave.calendar.manage",
    "leave.calendar.publish",
    "leave.record.manage",
    "leave.sla.manage",
    "leave.workflow_task.assign",
]

#: Keyed by the designation name as it exists in globals_designation.
ROLE_GRANTS = {
    "employee": _STUDENT_EMPLOYEE,
    "unit_head": _UNIT_HEAD,
    "sanctioning_authority": _SANCTIONING_AUTHORITY,
    "leave_administrator": _LEAVE_ADMINISTRATOR,
}
""
