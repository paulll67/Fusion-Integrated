"""Idempotent year-end balance transitions for the registered Leave models."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone


def process_year_end() -> int:
    """Lapse non-carry-forward balances and convert faculty VL to EL."""
    from modules.leave.models import LeaveAccount, LeaveLedgerEntry

    year = timezone.localdate().year
    processed = 0
    with transaction.atomic():
        accounts = LeaveAccount.objects.select_for_update().filter(year=year)
        for account in accounts:
            balance = Decimal(account.balance)
            if balance <= 0:
                continue

            if account.category in {"CL", "RH", "SCL"}:
                _record_once(
                    LeaveLedgerEntry,
                    user_id=account.user_id,
                    category=account.category,
                    year=year,
                    entry_type="YEAR_END_LAPSE",
                    amount=balance,
                    reason=f"Lapsed {account.category} balance at year end",
                )
                account.balance = 0
                account.save(update_fields=["balance", "updated_at"])
                processed += 1
            elif account.category == "VL" and account.is_faculty:
                converted = (balance * Decimal("0.5")).quantize(Decimal("0.01"))
                _record_once(
                    LeaveLedgerEntry,
                    user_id=account.user_id,
                    category="VL",
                    year=year,
                    entry_type="YEAR_END_VL_CONVERSION",
                    amount=balance,
                    reason=f"Converted {balance} VL to {converted} EL",
                )
                next_account, _ = LeaveAccount.objects.get_or_create(
                    user_id=account.user_id,
                    category="EL",
                    year=year + 1,
                    defaults={"balance": Decimal("0"), "is_faculty": True},
                )
                next_account.balance += converted
                next_account.save(update_fields=["balance", "updated_at"])
                account.balance = 0
                account.save(update_fields=["balance", "updated_at"])
                processed += 1

    return processed


def validate_year_end_calendar() -> int:
    """Count dates in the currently effective published calendar."""
    from modules.leave.models import HolidayRHCalendar

    today = timezone.localdate()
    calendar = (
        HolidayRHCalendar.objects.filter(
            is_published=True,
            effective_from__lte=today,
            effective_to__isnull=True,
        ).first()
        or HolidayRHCalendar.objects.filter(
            is_published=True,
            effective_from__lte=today,
            effective_to__gte=today,
        ).first()
    )
    if calendar is None:
        return 0
    return len(calendar.restricted_holidays) + len(calendar.holiday_markers)


def _record_once(model, **values) -> None:
    """Write the model's single allowed yearly adjustment without duplicates."""
    lookup = {
        "user_id": values["user_id"],
        "category": values["category"],
        "year": values["year"],
    }
    model.objects.get_or_create(**lookup, defaults=values)
