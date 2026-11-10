"""
Leave Management (ELM) — Public Contracts and Adapters.

The ONLY thing other modules may import from this file.
This module provides the public surface for accessing directory employees,
external Academic Calendar data, and leave-related aggregates without
cross-module database joins or direct table reads.

All identity references are integer user_id values. Cross-module data
access must use these public contracts (e.g., get_employees(),
get_vacation_periods()).
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fusion_auth.client import IamUnavailable, get_client
from modules.directory.models import UserRef


@dataclass(frozen=True)
class EmployeeDTO:
    """Employee projection for leave eligibility and balance checks."""
    user_id: int
    username: str
    display_name: str
    kind: str  # 'faculty' or 'staff'
    email: str = ""
    department: str = ""
    designation: str = ""
    batch_year: int | None = None
    
    @classmethod
    def from_ref(cls, r: UserRef) -> "EmployeeDTO":
        return cls(
            user_id=r.user_id,
            username=r.username,
            display_name=r.display_name,
            kind=r.kind,
            email=r.email,
            department=r.department,
            designation=r.designation or "",
            batch_year=r.batch_year,
        )


def get_employees(user_ids: Sequence[int] | None = None) -> dict[int, EmployeeDTO]:
    """Batched lookup of employees (faculty/staff).
    
    If user_ids is provided, returns only those users.
    Otherwise, returns all active employees for balance/eligibility checks.
    
    Returns a mapping where missing ids are absent from the result.
    """
    if user_ids:
        ids = {int(i) for i in user_ids if i is not None}
        if not ids:
            return {}
        # TODO: Use HR employment contract to filter by active employment status
        # from modules.hr.models import Employment
        # employees = UserRef.objects.filter(user_id__in=ids, employment__is_active=True)
        else:
            employees = UserRef.objects.filter(user_id__in=ids, is_active=True)
    else:
        employees = UserRef.objects.filter(kind__in=("faculty", "staff"), is_active=True)
    
    return {r.user_id: EmployeeDTO.from_ref(r) for r in employees.order_by("user_id")}


def get_employee(user_id: int) -> EmployeeDTO | None:
    """Singular lookup for a specific employee.
    
    Returns None if the user does not exist or is inactive.
    """
    try:
        r = UserRef.objects.get(user_id=user_id, is_active=True)
        return EmployeeDTO.from_ref(r)
    except UserRef.DoesNotExist:
        return None


def get_faculty() -> list[EmployeeDTO]:
    """Return all active faculty employees."""
    return [EmployeeDTO.from_ref(r) for r in UserRef.objects.filter(kind="faculty", is_active=True).order_by("user_id")]


def get_staff() -> list[EmployeeDTO]:
    """Return all active staff employees."""
    return [EmployeeDTO.from_ref(r) for r in UserRef.objects.filter(kind="staff", is_active=True).order_by("user_id")]


def held_employee_ids() -> set[int]:
    """Set of all active employee user IDs (faculty and staff)."""
    return {r.user_id for r in UserRef.objects.filter(kind__in=("faculty", "staff"), is_active=True)}


def get_users_in_discipline(discipline: str) -> list[int]:
    """Return user IDs of active students in a specific discipline."""
    return [r.user_id for r in UserRef.objects.filter(kind="student", discipline=discipline, is_active=True)]


def search_employees(q: str = "", kind: str | None = None) -> list[EmployeeDTO]:
    """Search employees by name or kind.
    
    Args:
        q: Search term for display_name.
        kind: Filter by 'faculty' or 'staff'.
    
    Returns:
        List of EmployeeDTO objects ordered by display_name.
    """
    qs = UserRef.objects.filter(is_active=True)
    if kind:
        qs = qs.filter(kind=kind)
    if q:
        qs = qs.filter(display_name__icontains=q)
    return [EmployeeDTO.from_ref(r) for r in qs.order_by("display_name")]


# --- External Data Contracts (No Direct DB Access) ---

def get_vacation_periods(year: int, faculty_user_id: int | None = None) -> list[dict]:
    """Fetch vacation periods for the Academic Calendar.
    
    This is a placeholder contract. In production, this should call
    an external service or module (e.g., modules.academic_calendar).
    
    Args:
        year: The academic year (e.g., 2026).
        faculty_user_id: Optional filter for specific faculty member's periods.
    
    Returns:
        List of dictionaries representing vacation periods with keys:
        - 'start_date': str (YYYY-MM-DD)
        - 'end_date': str (YYYY-MM-DD)
        - 'is_valid_for_leave': bool
    
    Raises:
        IamUnavailable: If the external service is unreachable.
    """
    # TODO: Implement actual call to Academic Calendar service
    # from modules.academic_calendar.client import get_calendar_service
    # try:
    #     service = get_calendar_service()
    #     return service.get_vacation_periods(year, faculty_user_id)
    # except IamUnavailable:
    #     raise
    
    # Fallback for local development / missing dependency:
    return []


def is_date_in_vacation_period(date_str: str, year: int) -> bool:
    """Check if a date falls within an applicable vacation period.
    
    Args:
        date_str: Date string in YYYY-MM-DD format.
        year: The academic year to check against.
    
    Returns:
        True if the date is within a published vacation period for the year.
    """
    # TODO: Implement actual logic using Academic Calendar data
    # periods = get_vacation_periods(year)
    # for p in periods:
    #     start, end = parse_dates(p['start_date'], p['end_date'])
    #     if start <= date_str <= end:
    #         return True
    return False


def get_restricted_holidays(year: int) -> list[dict]:
    """Fetch currently effective published Restricted Holidays.
    
    This is a placeholder contract. In production, this should call
    an external service or module (e.g., modules.academic_calendar).
    
    Returns:
        List of dictionaries representing holidays with keys:
        - 'date': str (YYYY-MM-DD)
        - 'name': str
    
    Raises:
        IamUnavailable: If the external service is unreachable.
    """
    # TODO: Implement actual call to Holiday/RH Calendar service
    # from modules.academic_calendar.client import get_calendar_service
    # try:
    #     service = get_calendar_service()
    #     return service.get_restricted_holidays(year)
    # except IamUnavailable:
    #     raise
    
    # Fallback for local development / missing dependency:
    return []


def is_date_restricted_holiday(date_str: str, year: int) -> bool:
    """Check if a date is a currently effective Restricted Holiday.
    
    Args:
        date_str: Date string in YYYY-MM-DD format.
        year: The academic year to check against.
    
    Returns:
        True if the date is a published RH for the year.
    """
    # TODO: Implement actual logic using Holiday/RH Calendar data
    holidays = get_restricted_holidays(year)
    return any(h['date'] == date_str for h in holidays)


# --- Utility Functions ---

def parse_date(date_str: str) -> tuple[int, int, int]:
    """Parse a date string into (year, month, day)."""
    try:
        return map(int, date_str.split("-"))
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}")


def is_leap_year(year: int) -> bool:
    """Check if a year is a leap year."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def days_in_month(year: int, month: int) -> int:
    """Get the number of days in a specific month."""
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    elif month in (4, 6, 9, 11):
        return 30
    elif month == 2:
        return 29 if is_leap_year(year) else 28
    else:
        raise ValueError(f"Invalid month: {month}")
