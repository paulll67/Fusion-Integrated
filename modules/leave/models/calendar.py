"""
Holiday and Restricted Holiday (RH) Calendar Administration Model.

This module provides the domain model for managing the currently effective published
holiday/RH calendar used by ELM for date and RH validation. It does not support
draft/publish/effective-version lifecycle; only the current published state is stored.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from core.db.mixins import TimeStampedModel, UserScopedModel


class HolidayRHCalendar(TimeStampedModel):
    """The currently effective published holiday/RH calendar.

    This aggregate represents the single source of truth for date and RH validation.
    Only one published state is maintained at any time. Historical versions are not
    stored to avoid complexity; new requests must validate against the current
    published calendar.

    Attributes:
        id: Unique identifier for the calendar instance.
        name: Display name of the calendar (e.g., 'Academic Year 2025-26 Holidays').
        effective_from: The date from which this calendar is effective.
        effective_to: The end date of validity (optional; if null, considered perpetual).
        holidays: List of dates marked as holidays.
        restricted_holidays: List of dates marked as Restricted Holidays (RH).
    """

    name = models.CharField(max_length=255, unique=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)  # Null implies perpetual validity
    holidays = models.JSONField(default=list, validators=[MinValueValidator(0)])
    restricted_holidays = models.JSONField(default=list, validators=[MinValueValidator(0)])

    class Meta:
        app_label = 'leave'
        verbose_name = 'Holiday/RH Calendar'
        verbose_name_plural = 'Holiday/RH Calendars'
        indexes = [
            models.Index(fields=['effective_from', 'effective_to']),
        ]

    def __str__(self) -> str:
        return f"{self.name} (Effective: {self.effective_from})"

    @classmethod
    def get_current(cls) -> "HolidayRHCalendar":
        """Retrieve the currently effective published calendar.

        Returns the calendar where the current date falls within [effective_from, effective_to].
        If no active calendar exists, raises a ValueError.
        """
        from datetime import date as dt_date

        today = dt_date.today()
        calendars = cls.objects.filter(effective_from__lte=today)

        if not calendars.exists():
            raise ValueError("No currently effective holiday/RH calendar found.")

        # If multiple exist (e.g., overlapping periods), pick the one with the latest start date
        # or the one that covers today most centrally. For simplicity, take the first match.
        return calendars.first()

    def is_holiday(self, check_date: date) -> bool:
        """Check if a specific date is marked as a holiday in this calendar.

        Args:
            check_date: The date to validate.

        Returns:
            True if the date is in the holidays list.
        """
        return check_date in self.holidays

    def is_restricted_holiday(self, check_date: date) -> bool:
        """Check if a specific date is marked as a Restricted Holiday (RH).

        Args:
            check_date: The date to validate.

        Returns:
            True if the date is in the restricted_holidays list.
        """
        return check_date in self.restricted_holidays

    def get_restricted_holiday_dates(self) -> list[date]:
        """Return a sorted list of Restricted Holiday dates.

        Returns:
            List of date objects.
        """
        return sorted(self.restricted_holidays)

    def is_valid_period(self, start_date: date, end_date: date) -> bool:
        """Validate if a leave period falls entirely within the calendar's validity range.

        Args:
            start_date: Start of the leave period.
            end_date: End of the leave period.

        Returns:
            True if the period is valid according to this calendar.
        """
        if self.effective_to and (start_date > self.effective_to or end_date > self.effective_to):
            return False
        return True
