"""
Leave Management (ELM) — Configuration Selectors and Adapters.

This module provides public selectors for current policy, hierarchy, published holiday/RH calendar,
and authorized admin listing. It implements BR-EL-030 (Current configured policy/hierarchy),
BR-EL-031 (Effective published holiday/RH calendar), and supports EL-UC-014/015 configuration access.

All identity references are integer user_id values. Cross-module data access uses public contracts
(e.g., get_policy_config(), get_holiday_calendar()). No cross-module FKs or direct table reads.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fusion_auth.client import IamUnavailable, get_client
from modules.directory.models import UserRef
from modules.directory.services.sync import ensure_users_cached


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


@dataclass(frozen=True)
class LeavePolicyConfigDTO:
    """Current leave entitlements and counting parameters.
    Implements BR-EL-030: Uses current configured values only; no draft/publish/effective-version lifecycle.
    """
    cl_days_per_year: int = 8
    rh_days_per_year: int = 2
    faculty_vl_conversion_enabled: bool = True
    half_day_cl_counting: bool = True


@dataclass(frozen=True)
class HierarchyConfigDTO:
    """Current org-unit/designation/category routing facts.
    Implements BR-EL-030: Uses current configured values only.
    """
    unit_head_role: str = "Unit Head"
    director_role: str = "Director"
    establishment_routing_enabled: bool = False


@dataclass(frozen=True)
class HolidayRHCalendarDTO:
    """Currently effective published holiday/RH calendar.
    Implements BR-EL-031: Only currently effective published calendar is used for date/RH validation.
    """
    name: str = "Default Calendar"
    holidays: list[tuple[int, str]] = ()  # (date_index, holiday_name)
    restricted_holidays: list[tuple[int, str]] = ()  # (date_index, rh_name)
    is_published: bool = False
    published_at: int | None = None


class ConfigurationSelectors:
    """Selectors for current policy, hierarchy, published holiday/RH calendar, and authorized admin listing.
    Provides public surface for accessing configuration data without cross-module database joins.
    """

    def __init__(self):
        self._policy_config: LeavePolicyConfigDTO | None = None
        self._hierarchy_config: HierarchyConfigDTO | None = None
        self._holiday_calendar: HolidayRHCalendarDTO | None = None
        self._admin_users: list[UserRef] = []

    async def get_policy_config(self) -> LeavePolicyConfigDTO:
        """Retrieve current leave policy configuration.
        Implements BR-EL-030: Uses current configured values only; no draft/publish/effective-version lifecycle.
        Returns the current LeavePolicyConfigDTO instance.
        """
        if self._policy_config is None:
            # TODO: Implement retrieval from configuration service or database (e.g., modules.hr)
            # For now, return defaults as per PS v1.4 §5/12 interpretation
            self._policy_config = LeavePolicyConfigDTO()
        return self._policy_config

    async def get_hierarchy_config(self) -> HierarchyConfigDTO:
        """Retrieve current hierarchy configuration used for validation and routing.
        Implements BR-EL-030: Uses current configured values only.
        Returns the current HierarchyConfigDTO instance.
        """
        if self._hierarchy_config is None:
            # TODO: Implement retrieval from configuration service or database (e.g., modules.hr)
            # For now, return defaults as per PS v1.4 §5/12 interpretation
            self._hierarchy_config = HierarchyConfigDTO()
        return self._hierarchy_config

    async def get_holiday_calendar(self) -> HolidayRHCalendarDTO:
        """Retrieve currently effective published holiday/RH calendar.
        Implements BR-EL-031: Only currently effective published calendar is used for date/RH validation.
        Returns the current HolidayRHCalendarDTO instance.
        """
        if self._holiday_calendar is None:
            # TODO: Implement retrieval from configuration service or database (e.g., modules.hr)
            # For now, return defaults as per PS v1.4 §5/12 interpretation
            self._holiday_calendar = HolidayRHCalendarDTO()
        return self._holiday_calendar

    async def get_authorized_admins(self) -> Sequence[EmployeeDTO]:
        """Retrieve list of authorized administrative users for leave record maintenance.
        Supports EL-UC-014/015 actor authorization checks.
        Returns a sequence of EmployeeDTO instances.
        """
        if not self._admin_users:
            # TODO: Implement retrieval from directory or HR service (e.g., modules.hr)
            # For now, return empty list as per PS v1.4 §5/12 interpretation
            self._admin_users = []
        return [EmployeeDTO.from_ref(u) for u in self._admin_users]

    async def refresh_all(self) -> None:
        """Refresh all configuration data from sources.
        Called when configuration changes are detected or on startup.
        """
        await self.get_policy_config()
        await self.get_hierarchy_config()
        await self.get_holiday_calendar()
        await self.get_authorized_admins()


class ConfigurationSelectorsAdapter:
    """Adapter to integrate ConfigurationSelectors into the Fusion platform.
    Provides a singleton-like interface for other modules to access configuration data.
    """

    _instance: ConfigurationSelectors | None = None

    @classmethod
    def get_instance(cls) -> ConfigurationSelectors:
        if cls._instance is None:
            cls._instance = ConfigurationSelectors()
        return cls._instance

    async def get_policy_config(self) -> LeavePolicyConfigDTO:
        return await ConfigurationSelectors.get_instance().get_policy_config()

    async def get_hierarchy_config(self) -> HierarchyConfigDTO:
        return await ConfigurationSelectors.get_instance().get_hierarchy_config()

    async def get_holiday_calendar(self) -> HolidayRHCalendarDTO:
        return await ConfigurationSelectors.get_instance().get_holiday_calendar()

    async def get_authorized_admins(self) -> Sequence[EmployeeDTO]:
        return await ConfigurationSelectors.get_instance().get_authorized_admins()

    async def refresh_all(self) -> None:
        await ConfigurationSelectors.get_instance().refresh_all()
