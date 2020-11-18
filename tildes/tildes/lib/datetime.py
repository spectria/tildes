# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions/classes related to dates and times."""

from __future__ import annotations
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from dateutil.rrule import rrule

from ago import human


class SimpleHoursPeriod:
    """A simple class that represents a time period of hours or days."""

    _SHORT_FORM_REGEX = re.compile(r"\d+[hd]", re.IGNORECASE)

    def __init__(self, hours: int):
        """Initialize a SimpleHoursPeriod from a number of hours."""
        if hours <= 0:
            raise ValueError("Period must be at least 1 hour.")

        self.hours = hours

        try:
            self.timedelta = timedelta(hours=hours)
        except OverflowError:
            raise ValueError("Time period is too large")

    @classmethod
    def from_short_form(cls, short_form: str) -> SimpleHoursPeriod:
        """Initialize a period from a "short form" string (e.g. "2h", "4d")."""
        if not cls._SHORT_FORM_REGEX.match(short_form):
            raise ValueError("Invalid time period")

        unit = short_form[-1].lower()
        count = int(short_form[:-1])

        if unit == "h":
            hours = count
        elif unit == "d":
            hours = count * 24

        return cls(hours=hours)

    def __str__(self) -> str:
        """Return a representation of the period as a string.

        Will be of the form "4 hours", "2 days", "1 day, 6 hours", etc. except for the
        special case of exactly "1 day", which is replaced with "24 hours".
        """
        string = human(self.timedelta, past_tense="{}")
        if string == "1 day":
            string = "24 hours"

        return string

    def __eq__(self, other: Any) -> bool:
        """Equality comparison method."""
        if isinstance(other, SimpleHoursPeriod):
            return self.hours == other.hours

        return NotImplemented

    def as_short_form(self) -> str:
        """Return a representation of the period as a "short form" string.

        Uses "hours" representation unless the period is an exact multiple of 24 hours
        (except for 24 hours itself).
        """
        if self.hours % 24 == 0 and self.hours != 24:
            return "{}d".format(self.hours // 24)

        return f"{self.hours}h"


def utc_now() -> datetime:
    """Return timezone-aware current datetime in UTC timezone."""
    return datetime.now(timezone.utc)


def utc_from_timestamp(timestamp: int) -> datetime:
    """Return timezone-aware datetime from a UTC timestamp."""
    return datetime.fromtimestamp(timestamp, timezone.utc)


def descriptive_timedelta(
    target: datetime, abbreviate: bool = False, precision: Optional[int] = None
) -> str:
    """Return a descriptive string for how long ago a datetime was.

    The returned string will be of a format like "4 hours ago" or "3 hours, 21 minutes
    ago". The second "precision level" is only added if it will be at least minutes, and
    only one "level" below the first unit.  That is, you'd never see anything like "4
    hours, 5 seconds ago" or "2 years, 3 hours ago".

    If `abbreviate` is true, the units will be shortened to return a string like
    "12h 28m ago" instead of "12 hours, 28 minutes ago".

    A time of less than a second returns "a moment ago".
    """
    # the ago library doesn't deal with timezones properly, so we need to calculate the
    # timedelta ourselves and only ever call human() using a timedelta
    delta = utc_now() - target

    seconds_ago = delta.total_seconds()
    if seconds_ago < 1:
        return "a moment ago"

    if not precision:
        # determine whether one or two precision levels is appropriate
        if seconds_ago < 3600:
            # if it's less than an hour, we always want only one precision level
            precision = 1
        else:
            # try a precision=2 version, and check the units it ends up with
            result = human(delta, precision=2)

            units = ("year", "day", "hour", "minute", "second")
            unit_indices = [i for (i, unit) in enumerate(units) if unit in result]

            # if there was only one unit in it, or they're adjacent, this is fine
            if len(unit_indices) < 2 or unit_indices[1] - unit_indices[0] == 1:
                precision = 2
            else:
                # otherwise, drop back down to precision=1
                precision = 1

    result = human(delta, precision, abbreviate=abbreviate)

    # remove commas if abbreviating ("3d 2h ago", not "3d, 2h ago")
    if abbreviate:
        result = result.replace(",", "")

    return result


def vague_timedelta_description(delta: timedelta) -> str:
    """Vaguely describe how long a timedelta refers to, like "over 2 weeks"."""
    if delta.days < 1:
        raise ValueError("The timedelta must be at least a day.")

    day_thresholds = {
        "year": 365,
        "month": 30,
        "week": 7,
        "day": 1,
    }

    for threshold, days in day_thresholds.items():
        if delta.days >= days:
            largest_threshold = threshold
            break

    count = str(delta.days // day_thresholds[largest_threshold])

    # set the strings we'll output based on count - change count of 1 to "a", otherwise
    # pluralize the threshold name (e.g. change "week" to "weeks")
    if count == "1":
        count = "a"
        period = largest_threshold
    else:
        period = largest_threshold + "s"

    return f"over {count} {period}"


def adaptive_date(
    target: datetime, abbreviate: bool = False, precision: Optional[int] = None
) -> str:
    """Return a date string that switches from relative to absolute past a threshold."""
    threshold = timedelta(days=7)

    # if the date is more recent than threshold, return the relative "ago"-style string
    if utc_now() - target < threshold:
        return descriptive_timedelta(target, abbreviate, precision)

    # if abbreviating, use the short version of month name ("Dec" instead of "December")
    if abbreviate:
        format_str = "%b %-d"
    else:
        format_str = "%B %-d"

    # only append the year if it's not the current year
    if target.year != utc_now().year:
        format_str += ", %Y"

    return target.strftime(format_str)


def rrule_to_str(rrule_obj: rrule) -> str:
    """Convert a dateutil rrule to its string definition.

    dateutil does this natively, but it always includes the start date, which we don't
    always need or want to be storing. This gives only the rrule definition.
    """
    return str(rrule_obj).split("RRULE:")[1]
