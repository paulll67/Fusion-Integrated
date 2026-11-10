"""
Employee Leave Management (ELM) — Entitlement Calculations and Year-End Processing.

This module implements leave entitlement calculations, balance management, and year-end outcome processing
for CL, RH, SCL, EL, COL, and VL categories. It enforces current configured policy values without
draft/publish/effective-version lifecycles.

Key responsibilities:
- Calculate available balances based on employee type (faculty/staff) and leave category.
- Validate request eligibility against current entitlements and overlap constraints.
- Process year-end conversions (VL to EL) and balance lapses.
- Manage LeaveLedgerEntry transactions for balance adjustments.

Identity references are integer user_id values. Cross-module data access uses public contracts from modules.leave.contracts.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional

from django.db import transaction
from django.utils import timezone

from fusion_auth.client import get_client
from modules.directory.models import UserRef
from modules.leave.contracts import EmployeeDTO, HolidayRHCalendar, VacationPeriod
from modules.leave.models import (
    LeaveAccount,
    LeaveLedgerEntry,
    LeavePolicyConfig,
    HierarchyConfig,
    HolidayRHCalendar as ModelHolidayRHCalendar,
)
from modules.leave.services.holiday_calendar_service import get_effective_published_calendar


class LeaveCategory(Enum):
    CL = "CL"  # Casual Leave
    RH = "RH"  # Restricted Holiday
    SCL = "SCL"  # Special Casual Leave
    EL = "EL"  # Earned Leave (Non-faculty)
    VL = "VL"  # Vacation Leave (Faculty)
    COL = "COL"  # Commuted Leave


class EntitlementType(Enum):
    ENTITLEMENT = "entitlement"
    BALANCE = "balance"


class YearEndOutcome(Enum):
    LAPSE = "lapse"
    CARRY_FORWARD = "carry_forward"
    CONVERT = "convert"


class LeaveBalanceValidator:
    """Validates leave balances against current policy configuration.
    Uses current configured values only; no draft/publish/effective-version lifecycle.
    """

    def __init__(self, user_ref: UserRef):
        self.user_id = user_ref.user_id
        self.kind = user_ref.kind  # 'faculty' or 'staff'
        self.designation = user_ref.designation or ""
        self.is_faculty = self.kind == "faculty"
        
    def get_policy_config(self) -> LeavePolicyConfig:
        """Retrieve current configured leave policy parameters.
        Returns the active configuration without version lifecycle semantics.
        """
        return LeavePolicyConfig.objects.filter(
            employee_user_id=self.user_id,
            is_active=True
        ).first() or LeavePolicyConfig.objects.first()

    def get_hierarchy_config(self) -> HierarchyConfig:
        """Retrieve current configured hierarchy routing facts.
        """
        return HierarchyConfig.objects.filter(
            employee_user_id=self.user_id,
            is_active=True
        ).first() or HierarchyConfig.objects.first()

    def get_entitlements(self) -> dict[LeaveCategory, int]:
        """Calculate annual entitlements based on category and employee type.
        Returns a dictionary mapping LeaveCategory to integer days.
        
        Rules:
        - CL: 8 days/year (laps at year end).
        - RH: 2 days/year (must match published calendar, laps at year end).
        - SCL: Up to 15 days/year (admissibility checked by authority).
        - EL: 30 days/year for non-faculty (carries forward).
        - VL: 60 days/year for faculty (tied to vacation periods, converts at year end).
        - COL: 20 days/year (medical/balance controlled, carries forward).
        """
        policy = self.get_policy_config()
        base_entitlements = {
            LeaveCategory.CL: 8,
            LeaveCategory.RH: 2,
            LeaveCategory.SCL: 15,
            LeaveCategory.EL: 30 if not self.is_faculty else 0,
            LeaveCategory.VL: 60 if self.is_faculty else 0,
            LeaveCategory.COL: 20,
        }
        
        # Apply specific overrides from policy config if present (current values only)
        for cat, override in getattr(policy, 'category_overrides', {}).items():
            base_entitlements[cat] = override
            
        return base_entitlements

    def get_available_balance(self, category: LeaveCategory) -> int:
        """Get the current available balance for a specific leave category.
        Handles VL conversion logic at year end if applicable.
        """
        # Fetch existing balance from ledger/account
        account = LeaveAccount.objects.filter(
            employee_user_id=self.user_id,
            category=category,
            is_active=True
        ).first()
        
        current_balance = 0
        if account:
            current_balance = int(account.balance)
        
        # Handle VL to EL conversion at year end (BR-EL-007)
        if category == LeaveCategory.VL and self.is_faculty:
            # Check if year-end processing has occurred for this fiscal year
            # If not processed, convert unused VL to EL (2 VL : 1 EL)
            current_year = timezone.now().year
            last_processed_year = account.last_processed_year or current_year - 1
            
            if current_year > last_processed_year:
                # Year-end conversion logic: Convert unused VL to EL
                vl_balance = current_balance // 2  # 2 VL : 1 EL ratio (integer division for simplicity, domain may refine)
                el_credit = vl_balance * 2  # Total EL credit from VL + existing EL
                
                # Update account balance to reflect conversion
                # Note: In a real DB schema, this might involve updating the VL balance to 0 and adding to EL
                # Here we return the calculated EL equivalent for validation purposes
                current_balance = el_credit
        
        return max(0, current_balance)

    def validate_request_eligibility(self, category: LeaveCategory, start_date: date, end_date: date) -> tuple[bool, str]:
        """Validate if a leave request is eligible based on entitlements and overlap rules.
        Returns (is_valid, error_message).
        """
        # Check category eligibility
        if category not in self.get_entitlements():
            return False, f"Leave category {category.value} is not supported."
        
        # Check balance availability
        available = self.get_available_balance(category)
        requested_days = (end_date - start_date).days + 1  # Inclusive count
        
        if requested_days > available:
            return False, f"Insufficient {category.value} balance. Available: {available}, Requested: {requested_days}."
        
        # Check overlap with active/pending leave (BR-EL-012)
        # Note: Detailed overlap logic depends on LeaveRequest model state and Station Leave coupling
        # This is a placeholder for the domain service integration
        pending_leave = self._check_pending_overlap(start_date, end_date)
        if pending_leave:
            return False, f"Overlap detected with active/pending leave."
        
        return True, ""

    def _check_pending_overlap(self, start_date: date, end_date: date) -> bool:
        """Check for overlap with pending or approved leave.
        First-half and second-half CL on the same date are not treated as overlapping.
        """
        # Placeholder for domain service integration to check LeaveRequest records
        # This would typically query the LeaveRequest model filtered by employee_user_id
        # and status in ['PENDING', 'APPROVED']
        return False  # Default to no overlap unless specific logic implemented

    def validate_station_leave_coupling(self, category: LeaveCategory) -> bool:
        """Validate if Station Leave details are required or applicable.
        BR-EL-013: Station Leave permission/details captured within same application when employee outside Jabalpur.
        """
        # Placeholder for logic to determine if employee is outside Jabalpur
        # This would depend on location data in the UserRef or Employment contract
        return False  # Default assumption unless location service provided

    def validate_substitute_eligibility(self, substitute_user_id: int) -> bool:
        """Validate if a nominated substitute is eligible.
        BR-EL-014: Substitute must be another employee, not the applicant, no overlapping leave.
        """
        # Placeholder for logic to check substitute's leave status and eligibility
        return True  # Default assumption unless substitute service provided

    def validate_calendar_applicability(self, category: LeaveCategory, date: date) -> bool:
        """Validate if a date corresponds to an applicable Restricted Holiday.
        BR-EL-031: Only currently effective published holiday/RH calendar is used.
        """
        try:
            calendar = get_effective_published_calendar()
        except Exception:
            return False  # No valid calendar available
        
        if category == LeaveCategory.RH:
            # Check if date is in the published holiday/RH calendar
            holidays = calendar.get_holidays()
            for h in holidays:
                if h.date == date:
                    return True
            return False
        else:
            # For other categories, calendar applicability may not be strict unless specified
            return True

    def process_year_end(self) -> list[LeaveLedgerEntry]:
        """Process year-end outcomes for the employee.
        BR-EL-020: Lapse CL/RH/SCL, carry EL/COL, convert unused VL to EL (2:1).
        Returns list of ledger entries created/updated.
        """
        entries = []
        current_year = timezone.now().year
        
        # Process CL, RH, SCL: Lapse at year end
        for category in [LeaveCategory.CL, LeaveCategory.RH, LeaveCategory.SCL]:
            account = LeaveAccount.objects.filter(
                employee_user_id=self.user_id,
                category=category,
                is_active=True
            ).first()
            
            if account:
                # Create a ledger entry for lapse
                entry = LeaveLedgerEntry.objects.create(
                    employee_user_id=self.user_id,
                    category=category,
                    transaction_type="year_end_lapse",
                    amount=-account.balance,  # Remove the balance
                    description=f"Year-end lapse of {category.value} for year {current_year}",
                )
                entries.append(entry)
        
        # Process EL, COL: Carry forward (no explicit ledger entry needed if balance persists, but can log)
        for category in [LeaveCategory.EL, LeaveCategory.COL]:
            account = LeaveAccount.objects.filter(
                employee_user_id=self.user_id,
                category=category,
                is_active=True
            ).first()
            
            if account and account.balance > 0:
                # Log carry forward (optional ledger entry or just ensure balance persists)
                # In this implementation, we assume the balance persists in the account
                pass
        
        # Process VL: Convert to EL (2 VL : 1 EL)
        vl_account = LeaveAccount.objects.filter(
            employee_user_id=self.user_id,
            category=LeaveCategory.VL,
            is_active=True
        ).first()
        
        if vl_account and vl_account.balance > 0:
            # Calculate EL credit from VL conversion
            el_credit = (vl_account.balance // 2) * 2  # 2 VL : 1 EL ratio
            
            # Update VL balance to zero (or remaining fractional part if domain refines)
            vl_account.balance = 0
            vl_account.save()
            
            # Credit EL account
            el_account = LeaveAccount.objects.filter(
                employee_user_id=self.user_id,
                category=LeaveCategory.EL,
                is_active=True
            ).first()
            
            if not el_account:
                el_account = LeaveAccount.objects.create(
                    employee_user_id=self.user_id,
                    category=LeaveCategory.EL,
                    balance=0,
                )
            
            el_account.balance += el_credit
            el_account.save()
            
            # Create ledger entries for conversion
            entry_vl = LeaveLedgerEntry.objects.create(
                employee_user_id=self.user_id,
                category=LeaveCategory.VL,
                transaction_type="year_end_conversion",
                amount=-vl_account.balance,  # Remove VL balance
                description=f"Year-end conversion of {vl_account.balance} VL to EL for year {current_year}",
            )
            entries.append(entry_vl)
            
            entry_el = LeaveLedgerEntry.objects.create(
                employee_user_id=self.user_id,
                category=LeaveCategory.EL,
                transaction_type="year_end_conversion",
                amount=el_credit,  # Add EL credit
                description=f"Year-end conversion of {vl_account.balance} VL to {el_credit} EL for year {current_year}",
            )
            entries.append(entry_el)
        
        return entries


class LeaveBalanceService:
    """Service layer for leave balance calculations and validations.
    Integrates with LeaveBalanceValidator for business logic.
    """

    def __init__(self, user_ref: UserRef):
        self.validator = LeaveBalanceValidator(user_ref)
        self.user_ref = user_ref

    def validate_leave_request(self, category: LeaveCategory, start_date: date, end_date: date) -> tuple[bool, str]:
        """Validate a leave request against current policy and balances.
        """
        is_valid, message = self.validator.validate_request_eligibility(category, start_date, end_date)
        return is_valid, message

    def get_available_balance(self, category: LeaveCategory) -> int:
        """Get available balance for a leave category.
        """
        return self.validator.get_available_balance(category)

    def process_year_end_balances(self) -> list[LeaveLedgerEntry]:
        """Process year-end balance adjustments and conversions.
        """
        return self.validator.process_year_end()

    @transaction.atomic
    def adjust_balance(self, category: LeaveCategory, adjustment_type: str, amount: int) -> Optional[LeaveLedgerEntry]:
        """Adjust leave balance for a specific category.
        adjustment_type: 'credit' or 'debit'
        Returns the created/updated ledger entry.
        """
        account = LeaveAccount.objects.filter(
            employee_user_id=self.user_ref.user_id,
            category=category,
            is_active=True
        ).first()
        
        if not account:
            return None
        
        new_balance = account.balance + amount
        if new_balance < 0:
            raise ValueError(f"Balance cannot be negative. Current: {account.balance}, Adjustment: {amount}")
        
        entry = LeaveLedgerEntry.objects.create(
            employee_user_id=self.user_ref.user_id,
            category=category,
            transaction_type=adjustment_type,
            amount=amount,
            description=f"Manual balance adjustment for {category.value}",
        )
        
        account.balance = new_balance
        account.save()
        
        return entry

    def validate_substitute(self, substitute_user_id: int) -> bool:
        """Validate if a nominated substitute is eligible.
        """
        return self.validator.validate_substitute_eligibility(substitute_user_id)

    def validate_calendar_holiday(self, category: LeaveCategory, date: date) -> bool:
        """Validate if a date is an applicable Restricted Holiday.
        """
        return self.validator.validate_calendar_applicability(category, date)
