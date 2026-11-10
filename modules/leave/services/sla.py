"""Idempotent reminder and escalation processing for leave workflow tasks."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

log = logging.getLogger("fusion.leave.sla")


@dataclass(frozen=True)
class SLAConfig:
    reminder_threshold_hours: int
    escalation_threshold_hours: int
    escalation_action: str


def get_sla_config() -> SLAConfig:
    """Read the current database configuration, with safe defaults."""
    from modules.leave.models import SLAConfig as SLAConfigModel

    config = SLAConfigModel.objects.order_by("-created_at").first()
    if config is None:
        return SLAConfig(48, 72, "notify")
    return SLAConfig(
        reminder_threshold_hours=config.reminder_threshold_hours,
        escalation_threshold_hours=config.escalation_threshold_hours,
        escalation_action=config.escalation_action,
    )


def process_sla_thresholds() -> int:
    """Queue threshold notifications and mark each one exactly once."""
    from modules.leave.models import WorkflowTask
    from modules.placement.models import NotificationOutbox

    config = get_sla_config()
    now = timezone.now()
    processed = 0

    tasks = WorkflowTask.objects.filter(state__in=("PENDING", "ASSIGNED"))
    for task in tasks.iterator():
        elapsed_hours = (now - task.created_at).total_seconds() / 3600
        if elapsed_hours < config.reminder_threshold_hours:
            continue

        with transaction.atomic():
            task_locked = WorkflowTask.objects.select_for_update().get(pk=task.pk)
            if task_locked.state not in {"PENDING", "ASSIGNED"}:
                continue

            if (
                elapsed_hours >= config.escalation_threshold_hours
                and not task_locked.escalation_triggered
            ):
                _enqueue(
                    NotificationOutbox,
                    topic="task.escalated",
                    dedupe_key=f"leave-task-escalation:{task_locked.pk}",
                    recipient_user_id=task_locked.assigned_user_id,
                    subject=f"Leave task escalation: {task_locked.task_kind}",
                    body="A pending leave task has crossed its escalation threshold.",
                )
                task_locked.escalation_triggered = True
                task_locked.save(update_fields=["escalation_triggered", "updated_at"])
                processed += 1
                continue

            if not task_locked.reminder_sent:
                _enqueue(
                    NotificationOutbox,
                    topic="task.reminder",
                    dedupe_key=f"leave-task-reminder:{task_locked.pk}",
                    recipient_user_id=task_locked.assigned_user_id,
                    subject=f"Leave task reminder: {task_locked.task_kind}",
                    body="A pending leave task is awaiting action.",
                )
                task_locked.reminder_sent = True
                task_locked.save(update_fields=["reminder_sent", "updated_at"])
                processed += 1

    return processed


def _enqueue(model, **values) -> None:
    """Create an outbox row while tolerating a concurrent idempotent insert."""
    try:
        model.objects.create(**values)
    except IntegrityError:
        log.debug("leave.sla.notification_already_queued key=%s", values["dedupe_key"])
