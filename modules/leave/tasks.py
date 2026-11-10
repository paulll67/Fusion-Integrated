"""
Employee Leave Management (ELM) â Scheduled Work Tasks.

Idempotent Celery task entry points for year-end and SLA threshold events.
These tasks do not add other scheduled behavior. They are designed to be
reliable, handling worker loss via `acks_late=True` and avoiding reprocessing
completed tasks where applicable.

Workflow authority: 06_ELM_Workflow_Specifications_v1.6_FINAL.docx (STTs).
Policy configuration: Follows Problem Statement v1.4 (current values only).
"""
from __future__ import annotations

import logging

from celery import shared_task

log = logging.getLogger("fusion.leave.tasks")


@shared_task(
    name="leave.process_year_end",
    acks_late=True, reject_on_worker_lost=True,
    soft_time_limit=300, time_limit=360,
)
def process_year_end() -> int:
    """Execute year-end leave processing (EL-UC-020).

    Applies lapse/carry-forward/VL-to-EL conversion rules based on current
    policy configuration. Records ledger entries and reports exceptions.

    Idempotency: Safe to run multiple times; only processes unprocessed
    year-end boundaries or pending adjustments.
    """
    from modules.leave.services import balances, ledgers, policies

    # Retrieve current policy configuration for lapse/carry rules
    policy_config = policies.get_current_policy()

    # Process leave accounts based on category-specific rules (CL/RH/SCL lapse,
    # EL/COL carry-forward, VL conversion)
    n_processed = balances.process_year_end_adjustments(policy_config=policy_config)

    # Record resulting ledger entries for all adjustments made
    ledgers.record_year_end_transactions(n_processed=n_processed)

    log.info("leave.year-end.processed count=%d", n_processed)
    return n_processed


@shared_task(
    name="leave.process_sla_thresholds",
    acks_late=True, reject_on_worker_lost=True,
    soft_time_limit=300, time_limit=360,
)
def process_sla_thresholds() -> int:
    """Process SLA threshold events (EL-UC-021).

    Checks pending actionable tasks against configured reminder and escalation
    thresholds. Sends notifications or performs configured escalation actions
    only if the task remains pending.

    Idempotency: Uses pending-state checks to avoid reprocessing completed tasks.
    """
    from modules.leave.services import sla, tasks

    # Retrieve current SLA configuration (thresholds and escalation actions)
    sla_config = sla.get_current_configuration()

    # Identify pending tasks that have crossed thresholds
    n_processed = sla.process_pending_tasks(sla_config=sla_config)

    log.info("leave.sla.processed count=%d", n_processed)
    return n_processed

