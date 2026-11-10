"""
Employee Leave Management (ELM) — Celery Beat Schedule and Task Routes.

This module defines the scheduled jobs and task routing for year-end processing,
SLA threshold monitoring, and other time-bound operations.

Workflow authority: 06_ELM_Workflow_Specifications_v1.6_FINAL.docx (STTs).
Policy configuration: Follows Problem Statement v1.4 (current values only).
"""
from celery.schedules import crontab, hourly

# Task routes map task names to worker queues.
# Without this, tasks queue on the default pool.
TASK_ROUTES = {
    "leave.process_year_end": {"queue": "reports"},
    "leave.process_sla_thresholds": {"queue": "notifications"},
    # SLA reminders can be sent frequently; keep them on a dedicated queue.
    "leave.send_sla_reminders": {"queue": "notifications"},
}

BEAT_SCHEDULE = {
    # Year-end leave processing.
    # Triggered at the configured year-end boundary (typically end of fiscal year).
    # Operation: Apply lapse/carry-forward/VL-to-EL conversion, write ledger entries, report exceptions.
    "leave.process_year_end": {
        "task": "leave.process_year_end",
        "schedule": crontab(hour=2, minute=0),
        "options": {"expires": 3600},
    },

    # SLA threshold processing.
    # Triggered periodically to check pending actionable tasks against configured thresholds.
    # Operation: Check pending tasks, send reminder/escalation only at configured thresholds, log outcome.
    "leave.process_sla_thresholds": {
        "task": "leave.process_sla_thresholds",
        "schedule": crontab(minute=0),
        "options": {"expires": 7200},
    },

    # SLA reminder dispatch.
    # Triggered frequently to ensure timely notification of pending tasks.
    "leave.send_sla_reminders": {
        "task": "leave.send_sla_reminders",
        "schedule": hourly(),
        "options": {"expires": 300},
    },
}
