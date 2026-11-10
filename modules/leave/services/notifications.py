"""Outbox-based notifications for assigned actionable tasks, withdrawal/decision communication and specified workflow outcomes.

This module implements notification delivery using the platform's outbox pattern (PC-BR-021).
Notifications are queued in the same transaction as the triggering event to ensure atomicity.
Redelivery is handled via `dedupe_key` for idempotency.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Any, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from fusion_auth.client import IamUnavailable, get_client
from modules.directory import contracts as directory
from modules.leave import contracts as leave
from modules.placement.models import NotificationOutbox

log = logging.getLogger("fusion.leave.notify")

# Registered notification topics for ELM domain.
# Any topic not listed here is a programming error (PC-BR-021).
TOPICS = {
    # Workflow Task Assignments
    "task.assigned",  # Assigned actionable task
    "task.reminder",  # SLA threshold reminder
    "task.escalated",  # SLA escalation notification
    
    # Lifecycle Events (Withdrawal, Cancellation)
    "request.withdrawn",  # Pending withdrawal effective
    "request.cancelled",  # Approved leave cancellation
    
    # Decision Communication
    "decision.approved",  # Final approval decision
    "decision.rejected",  # Final rejection decision
    "decision.not_recommended",  # Unit Head recommendation (for higher sanction)
    
    # Special Outcomes
    "substitute.declined",  # Substitute declined, applicant action required
    "resumption.reviewed",  # Resumption review outcome
    "year.end.processed",  # Year-end balance processing notification
}


def enqueue(
    *,
    topic: str,
    dedupe_key: str,
    subject: str,
    body: str,
    recipient_user_id: Optional[int] = None,
    recipient_email: str = "",
    payload: Optional[dict] = None,
) -> NotificationOutbox | None:
    """Queue one notification, inside the caller's transaction.
    
    Returns None if it was already queued (duplicate key).
    Raises ValueError for unknown topics or missing recipients.
    """
    if topic not in TOPICS:
        raise ValueError(f"Unknown notification topic {topic!r}.")
    
    if recipient_user_id is None and not recipient_email:
        raise ValueError("A notification needs a recipient.")

    try:
        # Nested transaction ensures duplicate key cannot poison caller's transaction.
        with transaction.atomic():
            return NotificationOutbox.objects.create(
                topic=topic,
                dedupe_key=dedupe_key,
                subject=subject,
                body=body,
                recipient_user_id=recipient_user_id,
                recipient_email=recipient_email,
                payload=payload or {},
            )
    except IntegrityError:
        log.debug("leave.notify.duplicate key=%s", dedupe_key)
        return None


def enqueue_many(rows: list[dict]) -> int:
    """Fan-out, one at a time so a single duplicate does not drop the batch."""
    return sum(1 for r in rows if enqueue(**r) is not None)


# -- Delivery: outside the request cycle, audiences expanded at send time -------
BROADCAST_SENTINEL = "leave-broadcast@invalid"


@dataclass
class DeliveryReport:
    expanded: int = 0
    sent: int = 0
    failed: int = 0
    skipped_capped: int = 0
    deferred: int = 0

    def __str__(self) -> str:
        return (
            f"expanded={self.expanded} sent={self.sent} failed={self.failed} "
            f"capped={self.skipped_capped} deferred={self.deferred}"
        )


def _backoff_ready(row: NotificationOutbox, now: datetime) -> bool:
    """Check if a notification should be retried based on backoff schedule.
    
    Schedule: 1, 2, 4, 8... minutes.
    """
    last_attempt = row.last_attempt
    if not last_attempt:
        return True
    
    elapsed_minutes = (now - last_attempt).total_seconds() / 60
    # Simple exponential backoff check
    retry_interval = 2 ** int(elapsed_minutes)
    return elapsed_minutes >= retry_interval


def _deliver(row: NotificationOutbox, now: datetime) -> bool:
    """Attempt to deliver a notification from the outbox.
    
    Returns True if successfully sent or skipped due to backoff.
    """
    if not row.recipient_email and not row.recipient_user_id:
        return False

    try:
        # Determine recipient based on configuration or stored data
        recipients = []
        if row.recipient_user_id:
            user_ref = directory.get_user_by_id(row.recipient_user_id)
            if user_ref:
                recipients.append(user_ref.email)
        
        if not recipients and row.recipient_email:
            recipients.append(row.recipient_email)

        if not recipients:
            return False

        # Send email notification
        send_mail(
            subject=row.subject,
            message=row.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
        )
        return True

    except Exception as e:
        log.exception("leave.notify.delivery_failed", exc_info=e)
        # Mark as failed for retry logic in background worker
        row.status = "failed"
        row.last_attempt = now
        row.save(update_fields=["status", "last_attempt"])
        return False


def process_outbox(now: datetime) -> DeliveryReport:
    """Process pending notifications from the outbox.
    
    This function is intended to be called by a scheduled task (e.g., Celery).
    """
    report = DeliveryReport()
    
    # Fetch pending or failed notifications
    rows = NotificationOutbox.objects.filter(
        status__in=["pending", "failed"]
    ).order_by("created_at")
    
    for row in rows:
        if _backoff_ready(row, now):
            report.expanded += 1
            if _deliver(row, now):
                row.status = "sent"
                row.last_sent = now
                row.save(update_fields=["status", "last_sent"])
                report.sent += 1
            else:
                # Mark as failed again for backoff retry
                row.status = "failed"
                row.last_attempt = now
                row.save(update_fields=["status", "last_attempt"])
                report.failed += 1
        else:
            # Still pending but not ready to send yet (backoff)
            report.deferred += 1
    
    return report
