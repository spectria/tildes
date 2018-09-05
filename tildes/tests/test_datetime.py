# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import datetime, timedelta, timezone

from tildes.lib.datetime import descriptive_timedelta, utc_now


def test_utc_now_has_timezone():
    """Ensure that utc_now() is returning a datetime with utc timezone."""
    dt = utc_now()
    assert dt.tzinfo == timezone.utc


def test_utc_now_accurate():
    """Ensure that utc_now() is returning an accurate UTC time."""
    utc_now_dt = utc_now().replace(tzinfo=None)
    datetime_dt = datetime.utcnow()

    assert (datetime_dt - utc_now_dt).total_seconds() < 1


def test_descriptive_timedelta_basic():
    """Ensure a simple descriptive timedelta works correctly."""
    test_time = utc_now() - timedelta(hours=3)
    assert descriptive_timedelta(test_time) == "3 hours ago"


def test_more_precise_longer_descriptive_timedelta():
    """Ensure a longer time period gets the extra precision level."""
    test_time = utc_now() - timedelta(days=2, hours=5)
    assert descriptive_timedelta(test_time) == "2 days, 5 hours ago"


def test_no_small_precision_descriptive_timedelta():
    """Ensure the extra precision doesn't apply to small units."""
    test_time = utc_now() - timedelta(days=6, minutes=10)
    assert descriptive_timedelta(test_time) == "6 days ago"


def test_single_precision_below_an_hour():
    """Ensure times under an hour only have one precision level."""
    test_time = utc_now() - timedelta(minutes=59, seconds=59)
    assert descriptive_timedelta(test_time) == "59 minutes ago"


def test_more_precision_above_an_hour():
    """Ensure the second precision level gets added just above an hour."""
    test_time = utc_now() - timedelta(hours=1, minutes=1)
    assert descriptive_timedelta(test_time) == "1 hour, 1 minute ago"


def test_subsecond_descriptive_timedelta():
    """Ensure time less than a second returns the special phrase."""
    test_time = utc_now() - timedelta(microseconds=100)
    assert descriptive_timedelta(test_time) == "a moment ago"


def test_above_second_descriptive_timedelta():
    """Ensure it starts describing time in seconds above 1 second."""
    test_time = utc_now() - timedelta(seconds=1, microseconds=100)
    assert descriptive_timedelta(test_time) == "1 second ago"
