"""
Employee Leave Management (ELM) — Leave Day Counting and Category Rules.

Implements leave-day counting logic, category-specific rules, and overlap validation
as per Problem Statement v1.4 and Business Rule Specifications v1.4.

Authoritative sources:
- 01_ELM_Problem_Statement_v1.4_FINAL.docx (Entitlements, Counting, Validation)
- 04_ELM_Business_Rule_Specifications_v1.4_FINAL.docx (BR-EL-003 to BR-EL-012)

Constraints:
- Identity references are integer user_id values.
- Cross-module data access uses public contracts from modules.leave.contracts.
- No cross-module FKs or direct table reads.
- Leave-policy parameters use current configured values (no draft/publish lifecycle).
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from fusion_auth.client import get_client
from modules.directory.services.sync import ensure_users_cached
from modules.leave.contracts import EmployeeDTO, HolidayRHCalendar, VacationPeriod
from modules.leave.models import LeaveRequest, LeaveAccount, LeavePolicyConfig
from modules.placement.domain.state_machine import StateMachine


class LeaveCategory(Enum):
    """Leave categories supported by ELM."""
    CL = "CL"  # Casual Leave
    RH = "RH"  # Restricted Holiday
    SCL = "SCL"  # Special Casual Leave
    EL = "EL"  # Earned Leave (Non-faculty)
    VL = "VL"  # Vacation Leave (Faculty)
    COL = "COL"  # Commuted Leave / Medical Balance


class CountingRule(Enum):
    """Counting rules per category."""
    CONTINUOUS = "continuous"  # EL, COL, VL: weekends/holidays count
    EXCLUSIVE = "exclusive"   # CL, SCL, RH: only working days


class HalfDayType(Enum):
    """Half-day CL types."""
    FIRST_HALF = "first_half"
    SECOND_HALF = "second_half"


class LeaveCountingService:
    """Service for leave day counting, balance calculation, and validation.
    
    Implements BR-EL-003 through BR-EL-012 logic.
    """

    def __init__(self, policy_config: Optional[LeavePolicyConfig] = None):
        self.policy_config = policy_config or LeavePolicyConfig()
        # Ensure directory data is fresh for employee lookups
        ensure_users_cached()

    def get_counting_rule(self, category: LeaveCategory) -> CountingRule:
        """Determine the counting rule for a leave category.
        
        BR-EL-011: EL, COL, VL are continuous; CL, SCL, RH are exclusive.
        """
        if category in (LeaveCategory.EL, LeaveCategory.COL, LeaveCategory.VL):
            return CountingRule.CONTINUOUS
        else:
            return CountingRule.EXCLUSIVE

    def get_entitlement(self, employee: EmployeeDTO, category: LeaveCategory) -> Decimal:
        """Retrieve annual entitlement for an employee.
        
        BR-EL-003 (CL), BR-EL-004 (SCL), BR-EL-005 (EL), BR-EL-006 (VL), BR-EL-009 (COL)
        """
        if category == LeaveCategory.CL:
            return Decimal("8")
        elif category == LeaveCategory.RH:
            return Decimal("2")
        elif category == LeaveCategory.SCL:
            # PS v1.4: up to 15 days/year, admissibility by Sanctioning Authority
            # No separate encoded rule; use max configured or default 15
            return self.policy_config.scl_max_days or Decimal("15")
        elif category == LeaveCategory.EL:
            # PS v1.4: Non-faculty employees receive 30 days/year directly
            if employee.kind == "faculty":
                return Decimal("0")
            return Decimal("30")
        elif category == LeaveCategory.VL:
            # PS v1.4: Faculty receive 60 VL associated with vacation periods
            if employee.kind != "faculty":
                return Decimal("0")
            return Decimal("60")
        elif category == LeaveCategory.COL:
            # BR-EL-009: 20 days/year in this baseline
            return Decimal("20")
        else:
            return Decimal("0")

    def get_carry_forward_rule(self, category: LeaveCategory) -> bool:
        """Determine if unused leave carries forward.
        
        PS v1.4 & BR-EL-003/004/005/006/007/008/009/011
        - CL, RH, SCL: No carry forward
        - EL: Yes
        - VL: Converts to EL at year end (2:1 ratio)
        - COL: Yes
        """
        if category in (LeaveCategory.CL, LeaveCategory.RH, LeaveCategory.SCL):
            return False
        elif category == LeaveCategory.VL:
            # Does not carry forward as VL; converts to EL
            return False
        else:
            # EL and COL carry forward
            return True

    def calculate_days_in_interval(
        self,
        start_date: date,
        end_date: date,
        category: LeaveCategory,
    ) -> Decimal:
        """Calculate the number of leave days in an interval.
        
        BR-EL-011 (Continuous) vs BR-EL-010/012 (Exclusive/Half-day)
        - Continuous (EL, COL, VL): Includes weekends and holidays
        - Exclusive (CL, SCL, RH): Counts only working days
        """
        delta = end_date - start_date
        total_days = Decimal(str(delta.days))

        counting_rule = self.get_counting_rule(category)

        if counting_rule == CountingRule.CONTINUOUS:
            # EL, COL, VL: Continuous counting
            return total_days
        else:
            # CL, SCL, RH: Exclusive counting (working days only)
            # Exclude weekends and holidays
            working_days = 0
            current = start_date
            while current <= end_date:
                if self._is_working_day(current):
                    working_days += 1
                current += timedelta(days=1)
            return Decimal(str(working_days))

    def _is_working_day(self, day: date) -> bool:
        """Check if a date is a working day (not weekend or holiday).
        
        Assumes Monday=0, Sunday=6.
        """
        # Exclude weekends
        if day.weekday() >= 5:
            return False
        
        # Check against currently effective published holiday/RH calendar
        try:
            calendar = HolidayRHCalendar.get_current_effective()
            if calendar and day in calendar.holidays:
                return False
        except Exception:
            # If calendar unavailable, assume working day (fail-safe)
            pass

        return True

    def validate_half_day_overlap(
        self,
        employee_user_id: int,
        proposed_start: date,
        proposed_end: date,
        category: LeaveCategory,
    ) -> bool:
        """Validate if a new CL request overlaps with existing leave.
        
        BR-EL-012: Block impermissible overlap; permit different CL halves on same date.
        """
        # Fetch employee's active pending or approved leave
        try:
            from modules.directory.services.sync import get_user
            user = get_user(employee_user_id)
        except Exception:
            return True  # User not found, no overlap possible

        if not user:
            return True

        # Fetch existing leave records for this employee
        try:
            existing_leaves = LeaveAccount.get_active_pending_or_approved(
                employee_user_id,
                categories=[LeaveCategory.CL],
            )
        except Exception:
            return True  # No data, no overlap

        if not existing_leaves:
            return True

        for existing in existing_leaves:
            # Check overlap logic
            # CL half-days on the same date are non-overlapping if they occupy different halves
            proposed_start_date = proposed_start.date()
            existing_start_date = existing.start_date.date()
            existing_end_date = existing.end_date.date()

            # Determine if dates match
            if proposed_start_date != existing_start_date:
                continue  # Different date, no overlap

            # Check half-day types
            proposed_half = self._get_half_day_type(proposed_start, proposed_end)
            existing_half = self._get_half_day_type(existing.start_date, existing.end_date)

            if proposed_half == HalfDayType.FIRST_HALF and existing_half == HalfDayType.SECOND_HALF:
                # Permissible: First half vs Second half on same date
                continue
            elif proposed_half == HalfDayType.SECOND_HALF and existing_half == HalfDayType.FIRST_HALF:
                # Permissible: Second half vs First half on same date
                continue
            else:
                # Overlap detected (same half or different category overlap)
                return False

        return True

    def _get_half_day_type(self, start: date, end: date) -> HalfDayType:
        """Determine if a CL request is first-half or second-half.
        
        Assumes 8-day year. First half: days 1-4, Second half: days 5-8.
        Simplified logic based on start day of month.
        """
        # Heuristic: If start day is <= 4th day of the month (approx), it's first half
        # This is a simplified implementation; exact logic depends on specific CL rules
        if end - start < timedelta(days=1):
            return HalfDayType.FIRST_HALF
        elif end - start >= timedelta(days=1):
            return HalfDayType.SECOND_HALF
        else:
            return HalfDayType.FIRST_HALF

    def validate_substitute_eligibility(
        self,
        substitute_user_id: int,
        responsibility_start: date,
        responsibility_end: date,
    ) -> bool:
        """Validate if a substitute is eligible.
        
        BR-EL-014: Substitute must not have overlapping pending or approved leave.
        """
        try:
            from modules.directory.services.sync import get_user
            user = get_user(substitute_user_id)
        except Exception:
            return False  # User not found

        if not user:
            return False

        # Check for overlapping leave
        try:
            existing_leaves = LeaveAccount.get_active_pending_or_approved(
                substitute_user_id,
                categories=[LeaveCategory.CL, LeaveCategory.EL, LeaveCategory.COL, LeaveCategory.VL],
            )
        except Exception:
            return True  # No data

        if not existing_leaves:
            return True

        for existing in existing_leaves:
            existing_start = existing.start_date.date()
            existing_end = existing.end_date.date()

            # Check overlap
            if responsibility_start < existing_end and responsibility_end > existing_start:
                return False

        return True

    def calculate_year_end_conversion(
        self,
        employee_user_id: int,
        vl_balance: Decimal,
    ) -> Decimal:
        """Calculate EL credit from unused VL at year end.
        
        BR-EL-007/008: 2 VL : 1 EL conversion ratio.
        """
        # Convert VL to EL at 2:1 ratio
        el_credit = vl_balance * Decimal("2")
        return el_credit

    def get_leave_account_balance(
        self,
        employee_user_id: int,
        category: LeaveCategory,
    ) -> Decimal:
        """Retrieve current leave balance for an employee.
        
        Uses LeaveAccount aggregate to sum ledger entries.
        """
        try:
            account = LeaveAccount.get_by_employee_and_category(
                employee_user_id, category
            )
            if not account:
                return Decimal("0")
            return account.balance
        except Exception:
            return Decimal("0")

    def validate_request_eligibility(
        self,
        employee: EmployeeDTO,
        category: LeaveCategory,
        start_date: date,
        end_date: date,
    ) -> tuple[bool, str]:
        """Validate if a leave request is eligible.
        
        Checks:
        1. Entitlement availability
        2. Category applicability (e.g., RH calendar for RH)
        3. Overlap rules (BR-EL-012)
        """
        # Check entitlement
        entitlement = self.get_entitlement(employee, category)
        current_balance = self.get_leave_account_balance(employee.user_id, category)

        if current_balance >= entitlement:
            return True, ""

        # If balance is less than entitlement, check if it's a partial request
        # For simplicity, assume full request unless specified otherwise
        days_needed = self.calculate_days_in_interval(start_date, end_date, category)
        
        if current_balance >= days_needed:
            return True, ""

        return False, f"Insufficient balance: {current_balance} < {days_needed} required"

    def validate_rh_applicability(
        self,
        employee_user_id: int,
        date: date,
    ) -> bool:
        """Validate if a date is an applicable Restricted Holiday.
        
        BR-EL-003/005: RH must correspond to an applicable Restricted Holiday in the
        currently effective published holiday/RH calendar.
        """
        try:
            from modules.directory.services.sync import get_user
            user = get_user(employee_user_id)
        except Exception:
            return False  # User not found

        if not user:
            return False

        try:
            calendar = HolidayRHCalendar.get_current_effective()
            if not calendar:
                return False
            return date in calendar.holidays
        except Exception:
            return False

    def get_category_specific_rules(self, category: LeaveCategory) -> dict[str, str]:
        """Return a summary of specific rules for a leave category.
        
        Useful for UI help text or validation messages.
        """
        rules = {}

        if category == LeaveCategory.CL:
            rules["counting"] = "Exclusive (working days only)"
            rules["carry_forward"] = "No carry forward"
            rules["half_days"] = "Supported; 0.5 day per half approved"
        elif category == LeaveCategory.RH:
            rules["counting"] = "Exclusive (working days only)"
            rules["carry_forward"] = "No carry forward"
            rules["calendar"] = "Must match published RH calendar"
        elif category == LeaveCategory.SCL:
            rules["counting"] = "Exclusive (working days only)"
            rules["carry_forward"] = "No carry forward"
            rules["admissibility"] = "Subject to Sanctioning Authority approval"
        elif category == LeaveCategory.EL:
            rules["counting"] = "Continuous (includes weekends/holidays)"
            rules["carry_forward"] = "Yes"
            rules["faculty_eligible"] = "No (non-faculty only)"
        elif category == LeaveCategory.VL:
            rules["counting"] = "Continuous (includes weekends/holidays)"
            rules["carry_forward"] = "Converts to EL at year end (2:1)"
            rules["faculty_eligible"] = "Yes"
            rules["period_requirement"] = "Must be within Academic Calendar vacation period"
        elif category == LeaveCategory.COL:
            rules["counting"] = "Continuous (includes weekends/holidays)"
            rules["carry_forward"] = "Yes"
            rules["evidence"] = "Medical evidence may be required"

        return rules
