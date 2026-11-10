"""Celery entry points for scheduled Employee Leave Management work."""

from __future__ import annotations

import logging

from celery import shared_task

log = logging.getLogger("fusion.leave.tasks")


@shared_task(
    name="leave.process_year_end",
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=300,
    time_limit=360,
)
def process_year_end() -> int:
    """Apply the idempotent year-end balance transition."""
    from modules.leave.services.year_end import process_year_end as run_year_end

    count = run_year_end()
    log.info("leave.year_end.processed count=%d", count)
    return count


@shared_task(
    name="leave.process_sla_thresholds",
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=300,
    time_limit=360,
)
def process_sla_thresholds() -> int:
    """Send one reminder/escalation for each threshold-crossing task."""
    from modules.leave.services.sla import process_sla_thresholds as run_sla

    count = run_sla()
    log.info("leave.sla.processed count=%d", count)
    return count


@shared_task(
    name="leave.send_sla_reminders",
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=300,
    time_limit=360,
)
def send_sla_reminders() -> int:
    """Dispatch due reminders using the same idempotent SLA processor."""
    return process_sla_thresholds()
