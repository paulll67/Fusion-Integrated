"""Year-end leave processing.

Idempotent ledger updates for category lapse, EL/COL carry-forward and faculty VL-to-EL conversion.
Per Problem Statement v1.4: uses current configured policy values without draft/publish/effective-version lifecycle.
Per Workflow Specifications v1.6: triggers on year-end boundary event; records outcomes in LeaveLedgerEntry.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Sequence

from celery import shared_task
from django.db import transaction
from django.utils import timezone

log = logging.getLogger("fusion.leave.year_end")


@shared_task(
    name="leave.process_year_end",
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=300,
)
def process_year_end() -> int:
    """Execute year-end leave processing (EL-UC-020).

    Applies category lapse rules, converts unused faculty VL to EL,
    and carries forward EL/COL balances. Records all outcomes in the ledger.
    """
    from modules.leave.models import (
        LeaveAccount,
        LeaveLedgerEntry,
        LeaveRequest,
        HolidayRHCalendar,
        VacationPeriod,
    )
    from modules.directory.services.sync import get_employees_cached

    # Use current configured policy values (no draft/publish lifecycle)
    # Policy constants are assumed to be defined in the domain or config module
    CL_ENTITLEMENT = 8
    RH_ENTITLEMENT = 2
    COL_ENTITLEMENT = 20
    VL_TO_EL_RATIO = 2  # 2 VL : 1 EL

    n_processed = 0

    with transaction.atomic():
        # Identify employees requiring processing
        employees = get_employees_cached()

        for emp in employees:
            user_id = emp.user_id
            kind = emp.kind
            
            # Process Casual Leave (CL) - Lapse unused days
            cl_account = LeaveAccount.objects.filter(
                employee_user_id=user_id,
                category="CL",
                year_end_date=timezone.now().date()
            ).first()
            
            if cl_account:
                n_lapsed = max(0, CL_ENTITLEMENT - cl_account.balance)
                if n_lapsed > 0:
                    # Record lapse transaction
                    entry = LeaveLedgerEntry.objects.create(
                        employee_user_id=user_id,
                        category="CL",
                        transaction_type="LAPSE",
                        amount=-n_lapsed,
                        description=f"Year-end CL lapse: {n_lapsed} days",
                        year_end_date=timezone.now().date(),
                    )
                    n_processed += 1
                
                # Reset balance to entitlement
                cl_account.balance = CL_ENTITLEMENT
                cl_account.save(update_fields=["balance"])

            # Process Restricted Holiday (RH) - Lapse unused days
            rh_account = LeaveAccount.objects.filter(
                employee_user_id=user_id,
                category="RH",
                year_end_date=timezone.now().date()
            ).first()
            
            if rh_account:
                n_lapsed = max(0, RH_ENTITLEMENT - rh_account.balance)
                if n_lapsed > 0:
                    entry = LeaveLedgerEntry.objects.create(
                        employee_user_id=user_id,
                        category="RH",
                        transaction_type="LAPSE",
                        amount=-n_lapsed,
                        description=f"Year-end RH lapse: {n_lapsed} days",
                        year_end_date=timezone.now().date(),
                    )
                    n_processed += 1
                
                rh_account.balance = RH_ENTITLEMENT
                rh_account.save(update_fields=["balance"])

            # Process Special Casual Leave (SCL) - Lapse unused days
            scl_account = LeaveAccount.objects.filter(
                employee_user_id=user_id,
                category="SCL",
                year_end_date=timezone.now().date()
            ).first()
            
            if scl_account:
                n_lapsed = max(0, 15 - scl_account.balance)  # Max 15 days per spec
                if n_lapsed > 0:
                    entry = LeaveLedgerEntry.objects.create(
                        employee_user_id=user_id,
                        category="SCL",
                        transaction_type="LAPSE",
                        amount=-n_lapsed,
                        description=f"Year-end SCL lapse: {n_lapsed} days",
                        year_end_date=timezone.now().date(),
                    )
                    n_processed += 1
                
                scl_account.balance = min(15, scl_account.balance)
                scl_account.save(update_fields=["balance"])

            # Process Earned Leave (EL) - Carry forward
            el_account = LeaveAccount.objects.filter(
                employee_user_id=user_id,
                category="EL",
                year_end_date=timezone.now().date()
            ).first()
            
            if el_account:
                # EL carries forward, no lapse
                # Ensure balance is non-negative and consistent with previous year end
                el_account.balance = max(0, el_account.balance)
                el_account.save(update_fields=["balance"])

            # Process Commuted Leave (COL) - Carry forward
            col_account = LeaveAccount.objects.filter(
                employee_user_id=user_id,
                category="COL",
                year_end_date=timezone.now().date()
            ).first()
            
            if col_account:
                # COL carries forward, no lapse
                col_account.balance = max(0, col_account.balance)
                col_account.save(update_fields=["balance"])

            # Process Vacation Leave (VL) - Faculty only, convert to EL
            if kind == "faculty":
                vl_account = LeaveAccount.objects.filter(
                    employee_user_id=user_id,
                    category="VL",
                    year_end_date=timezone.now().date()
                ).first()
                
                if vl_account:
                    # VL does not carry forward; convert to EL
                    n_vl = vl_account.balance
                    n_el_converted = int(n_vl * VL_TO_EL_RATIO)
                    
                    if n_el_converted > 0:
                        # Record conversion transaction
                        entry = LeaveLedgerEntry.objects.create(
                            employee_user_id=user_id,
                            category="VL",
                            transaction_type="CONVERT_TO_EL",
                            amount=-n_vl,  # Remove VL
                            description=f"Year-end VL to EL conversion: {n_vl} VL -> {n_el_converted} EL",
                            year_end_date=timezone.now().date(),
                        )
                        n_processed += 1
                        
                        # Update VL balance to zero
                        vl_account.balance = 0
                        vl_account.save(update_fields=["balance"])
                        
                        # Credit converted EL to employee's EL account
                        el_credit_entry = LeaveLedgerEntry.objects.create(
                            employee_user_id=user_id,
                            category="EL",
                            transaction_type="CREDIT_FROM_VL",
                            amount=n_el_converted,
                            description=f"Year-end VL conversion credit: {n_el_converted} EL",
                            year_end_date=timezone.now().date(),
                        )
                        
                        # Update EL balance
                        el_account.balance += n_el_converted
                        el_account.save(update_fields=["balance"])

    log.info("leave.year_end.processed employees=%d", n_processed)
    return n_processed


@shared_task(
    name="leave.validate_year_end_calendar",
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=120,
)
def validate_year_end_calendar() -> int:
    """Validate holiday/RH calendar for year-end processing (BR-EL-031).

    Ensures the currently effective published calendar is available.
    """
    from modules.leave.models import HolidayRHCalendar
    
    # Check if a valid, published calendar exists
    current_calendar = HolidayRHCalendar.objects.filter(
        publication_state="published",
        is_current=True
    ).first()
    
    if not current_calendar:
        log.warning("No active holiday/RH calendar found for year-end processing")
        return 0
    
    # Validate date ranges against the calendar
    n_validated = 0
    for date_obj in HolidayRHCalendar.objects.filter(
        publication_state="published",
        is_current=True
    ).values_list("date", flat=True):
        try:
            d = date_obj
            if d <= timezone.now().date():
                n_validated += 1
        except ValueError:
            continue
    
    log.info("leave.calendar.validated dates=%d", n_validated)
    return n_validated
