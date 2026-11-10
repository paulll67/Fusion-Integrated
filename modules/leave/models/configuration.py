"""
Employee Leave Management (ELM) — Configuration and Hierarchy Models.

This module defines the current configured leave-policy parameters,
hierarchy/routing configuration, and SLA thresholds. It does not implement
a draft/publish/effective-version lifecycle; values are treated as current
and active unless explicitly marked otherwise in the database schema.

Identity references use integer user_id values. Cross-module data access
must use public contracts defined in modules.leave.contracts.py.
"""

from decimal import Decimal
from typing import Any

from django.db import models

from core.db.mixins import TimeStampedModel

CATEGORY_CL = "CL"
CATEGORY_RH = "RH"
CATEGORY_SCL = "SCL"
CATEGORY_EL = "EL"
CATEGORY_COL = "COL"
CATEGORY_VL = "VL"

# =============================================================================
# Leave Policy Configuration
# =============================================================================


class LeavePolicyConfig(TimeStampedModel):
    """Current leave entitlements and counting parameters.

    This model stores the active policy values used for validation and
    balance calculations. Per Problem Statement v1.4, there is no
    draft/publish/effective-version lifecycle; these are current configured
    values only.

    Attributes:
        - CL: 8 days/year (no carry-forward)
        - RH: 2 days/year (calendar-dependent, no carry-forward)
        - SCL: Up to 15 days/year (authority-dependent, no carry-forward)
        - EL: 30 days/year for non-faculty (carry-forward enabled)
        - VL: 60 days/year for faculty (vacation-period dependent, converts to EL at year-end)
        - COL: 20 days/year (carry-forward enabled)
    """

    # Leave Category Codes
    CATEGORY_CL = "CL"
    CATEGORY_RH = "RH"
    CATEGORY_SCL = "SCL"
    CATEGORY_EL = "EL"
    CATEGORY_COL = "COL"
    CATEGORY_VL = "VL"

    # Entitlements (days per year)
    ENTITLEMENT_CL = 8
    ENTITLEMENT_RH = 2
    ENTITLEMENT_SCL = 15
    ENTITLEMENT_EL = 30
    ENTITLEMENT_COL = 20
    ENTITLEMENT_VL = 60

    # Counting Rules
    COUNTING_CONTINUOUS_CATEGORIES = [CATEGORY_EL, CATEGORY_COL, CATEGORY_VL]
    COUNTING_DISCRETE_CATEGORIES = [CATEGORY_CL, CATEGORY_RH, CATEGORY_SCL]

    class Meta:
        db_table = "leave_policy_config"
        verbose_name = "Leave Policy Configuration"

    # Leave Category fields
    category_cl_days = models.PositiveSmallIntegerField(default=ENTITLEMENT_CL)
    category_rh_days = models.PositiveSmallIntegerField(default=ENTITLEMENT_RH)
    category_scl_days = models.PositiveSmallIntegerField(default=ENTITLEMENT_SCL)
    category_el_days = models.PositiveSmallIntegerField(default=ENTITLEMENT_EL)
    category_col_days = models.PositiveSmallIntegerField(default=ENTITLEMENT_COL)
    category_vl_days = models.PositiveSmallIntegerField(default=ENTITLEMENT_VL)

    # VL conversion ratio at year-end (2 VL : 1 EL)
    vl_to_el_conversion_ratio = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("0.5")
    )

    # Year-end processing flags
    lapse_unused_cl = models.BooleanField(default=True)
    lapse_unused_rh = models.BooleanField(default=True)
    lapse_unused_scl = models.BooleanField(default=True)
    carry_forward_el = models.BooleanField(default=True)
    carry_forward_col = models.BooleanField(default=True)
    convert_vl_to_el_at_year_end = models.BooleanField(default=True)

    # Validation thresholds (days)
    min_cl_days_for_half_day = models.PositiveSmallIntegerField(default=1)
    max_scl_days_per_request = models.PositiveSmallIntegerField(default=15)

    def __str__(self) -> str:
        return "Leave Policy Config"


# =============================================================================
# Hierarchy and Routing Configuration
# =============================================================================


class HierarchyConfig(TimeStampedModel):
    """Current organizational unit and designation routing configuration.

    Defines the hierarchy path for leave sanctioning based on employee
    designation, organizational unit, and leave category. No versioning;
    values are current active settings.

    Routing Logic:
        - CL/RH: Unit Head is final authority (unless overridden by policy).
        - SCL/EL/COL/VL: Unit Head records recommendation -> Sanctioning Authority.
        - Director Self-Sanction: Special rule for Director's own leave.
    """

    # Role Codes
    ROLE_UNIT_HEAD = "UNIT_HEAD"
    ROLE_DEPUTY_REGISTRAR = "DEPUTY_REGISTRAR"
    ROLE_DEAN = "DEAN"
    ROLE_REGISTRAR = "REGISTRAR"
    ROLE_DIRECTOR = "DIRECTOR"

    # Designation Codes (example set)
    DESIGNATION_FACULTY = "FACULTY"
    DESIGNATION_STAFF = "STAFF"
    DESIGNATION_DEPUTY_REGISTRAR = "DEPUTY_REGISTRAR"
    DESIGNATION_DEAN = "DEAN"
    DESIGNATION_REGISTRAR = "REGISTRAR"
    DESIGNATION_DIRECTOR = "DIRECTOR"

    # Leave Category Codes
    CATEGORY_CL = "CL"
    CATEGORY_RH = "RH"
    CATEGORY_SCL = "SCL"
    CATEGORY_EL = "EL"
    CATEGORY_COL = "COL"
    CATEGORY_VL = "VL"

    class Meta:
        db_table = "hierarchy_config"
        verbose_name = "Hierarchy Configuration"

    # Routing configuration per designation/leave category combination
    # Structure: {designation_code: {leave_category: [role_codes]}}
    routing_rules = models.JSONField(default=dict, blank=True)

    # Example structure:
    # {
    #     "FACULTY": {
    #         "CL": ["UNIT_HEAD"],
    #         "RH": ["UNIT_HEAD"],
    #         "SCL": ["UNIT_HEAD", "DEPUTY_REGISTRAR"],
    #         "EL": ["UNIT_HEAD", "DEPUTY_REGISTRAR"],
    #         "COL": ["UNIT_HEAD", "DEPUTY_REGISTRAR"],
    #         "VL": ["UNIT_HEAD", "DEPUTY_REGISTRAR"]
    #     },
    #     "STAFF": {
    #         "CL": ["UNIT_HEAD"],
    #         "RH": ["UNIT_HEAD"],
    #         "SCL": ["UNIT_HEAD", "DEPUTY_REGISTRAR"],
    #         "EL": ["UNIT_HEAD", "DEPUTY_REGISTRAR"],
    #         "COL": ["UNIT_HEAD", "DEPUTY_REGISTRAR"],
    #         "VL": ["UNIT_HEAD", "DEPUTY_REGISTRAR"]
    #     },
    #     "DIRECTOR": {
    #         "CL": ["DIRECTOR"],
    #         "RH": ["DIRECTOR"],
    #         "SCL": ["DIRECTOR"],
    #         "EL": ["DIRECTOR"],
    #         "COL": ["DIRECTOR"],
    #         "VL": ["DIRECTOR"]
    #     }
    # }

    # Establishment processing flag (optional step in hierarchy)
    enable_establishment_routing = models.BooleanField(default=False)

    def get_routing_path(self, designation: str, category: str) -> list[str]:
        """Retrieve the sanctioning path for a given designation and leave category.

        Args:
            designation (str): Employee designation code.
            category (str): Leave category code.

        Returns:
            List of role codes in order of approval.
        """
        rules = self.routing_rules.get(designation, {})
        return rules.get(category, [self.ROLE_UNIT_HEAD])

    def __str__(self) -> str:
        return "Hierarchy Config"


# =============================================================================
# SLA Threshold Configuration
# =============================================================================


class SLAConfig(TimeStampedModel):
    """SLA threshold and escalation configuration.

    Defines reminder and escalation thresholds for pending actionable tasks.
    Values are current configured settings used by event-triggered processing.

    Per Business Rule BR-EL-038, these thresholds are configurable.
    """

    # Thresholds in hours
    reminder_threshold_hours = models.PositiveSmallIntegerField(default=48)
    escalation_threshold_hours = models.PositiveSmallIntegerField(default=24)

    # Escalation action configuration
    # Options: "notify", "escalate_to_director", "auto_reject" (if supported by workflow)
    escalation_action = models.CharField(max_length=50, blank=True, default="notify")

    class Meta:
        db_table = "sla_config"
        verbose_name = "SLA Configuration"

    def __str__(self) -> str:
        return f"SLA Config (Rem: {self.reminder_threshold_hours}h, Esc: {self.escalation_threshold_hours}h)"


# =============================================================================
# Calendar and Holiday Configuration
# =============================================================================


class HolidayRHCalendar(TimeStampedModel):
    """Holiday/RH calendar metadata and date records.

    Stores the currently effective published holiday and Restricted Holiday (RH)
    dates used for validation. Only published calendars are considered active.

    Per Problem Statement v1.4, there is no draft/publish/effective-version
    lifecycle for policy parameters; however, calendar publication state
    is tracked here to determine applicability.

    Attributes:
        - dates: List of date objects (YYYY-MM-DD)
        - rh_marker: Boolean indicating if the date is a Restricted Holiday
        - published_at: Timestamp when the calendar was published
    """

    # Calendar metadata
    name = models.CharField(max_length=100, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    # Date records
    dates = models.JSONField(default=list, blank=True)
    # Each date record: {"date": "YYYY-MM-DD", "rh_marker": bool}

    class Meta:
        db_table = "holiday_rh_calendar"
        verbose_name = "Holiday/RH Calendar"

    def get_published_dates(self) -> list[dict[str, Any]]:
        """Return only the dates from a published calendar.

        Returns:
            List of date dictionaries with 'date' and 'rh_marker' keys.
        """
        if not self.is_published:
            return []
        return self.dates

    def get_rh_dates(self) -> list[dict[str, Any]]:
        """Return only the Restricted Holiday dates from a published calendar.

        Returns:
            List of date dictionaries where 'rh_marker' is True.
        """
        return [d for d in self.dates if d.get("rh_marker", False)]

    def __str__(self) -> str:
        return f"{self.name} ({self.year})"


# =============================================================================
# Offline Sanction Record Configuration
# =============================================================================


class OfflineSanctionRecord(TimeStampedModel):
    """Record for already-sanctioned offline leave.

    Used to synchronize an already-authorized paper/offline leave with the
    system without issuing a second sanction. Per BR-EL-029, this is for
    record integrity and synchronization only.

    Attributes:
        - employee_user_id: The employee who took the leave.
        - category: Leave category code.
        - start_date / end_date: Actual leave interval.
        - sanction_reference: Reference to the original offline sanction document.
        - consistency_outcome: Result of synchronization (e.g., "matched", "adjusted").
    """

    employee_user_id = models.PositiveIntegerField(unique=True)
    category = models.CharField(
        max_length=10,
        choices=[
            (c, c)
            for c in [
                CATEGORY_CL,
                CATEGORY_RH,
                CATEGORY_SCL,
                CATEGORY_EL,
                CATEGORY_COL,
                CATEGORY_VL,
            ]
        ],
    )
    start_date = models.DateField()
    end_date = models.DateField()
    sanction_reference = models.CharField(max_length=255, blank=True)
    consistency_outcome = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "offline_sanction_record"
        verbose_name = "Offline Sanction Record"

    def __str__(self) -> str:
        return f"Offline Sanction for {self.employee_user_id} ({self.category})"


# =============================================================================
# Leave Account and Ledger Entry Configuration
# =============================================================================


class LeaveAccount(TimeStampedModel):
    """Employee leave account aggregate.

    Tracks balances for each leave category per employee. Balances are derived
    from explicit ledger entries (approvals, extensions, cancellations, etc.).

    Attributes:
        - employee_user_id: The employee.
        - category: Leave category code.
        - balance: Current available days.
        - year_start_date: Start of the fiscal/academic year for this account.
    """

    employee_user_id = models.PositiveIntegerField(unique=True)
    category = models.CharField(
        max_length=10,
        choices=[
            (c, c)
            for c in [
                CATEGORY_CL,
                CATEGORY_RH,
                CATEGORY_SCL,
                CATEGORY_EL,
                CATEGORY_COL,
                CATEGORY_VL,
            ]
        ],
    )
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    year_start_date = models.DateField()

    class Meta:
        db_table = "leave_account"
        verbose_name = "Leave Account"

    def __str__(self) -> str:
        return f"{self.employee_user_id} - {self.category}: {self.balance}"


class LeaveLedgerEntry(TimeStampedModel):
    """Explicit ledger entry for leave balance changes.

    Records the source of a balance change (e.g., approval, extension,
    cancellation, resumption adjustment, year-end conversion).

    Attributes:
        - account: Reference to the LeaveAccount affected.
        - transaction_type: Type of change (APPROVAL, EXTENSION, CANCELLATION, etc.).
        - amount_change: Positive for credit, negative for debit.
        - source_reference: Link to original request or event.
    """

    account = models.ForeignKey(LeaveAccount, on_delete=models.CASCADE)
    transaction_type = models.CharField(
        max_length=50,
        choices=[
            (t, t)
            for t in [
                "APPROVAL",
                "EXTENSION",
                "CANCELLATION",
                "RESUMPTION_ADJUSTMENT",
                "YEAR_END_CONVERSION",
                "LAPSE",
            ]
        ],
    )
    amount_change = models.DecimalField(max_digits=8, decimal_places=2)
    source_reference = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "leave_ledger_entry"
        verbose_name = "Leave Ledger Entry"

    def __str__(self) -> str:
        return f"{self.account} - {self.transaction_type}: {self.amount_change}"
