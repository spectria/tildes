# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import timedelta

from pytest import raises

from tildes.scrapers import YoutubeScraper


def test_youtube_duration_parsing():
    """Ensure a simple Youtube duration parses successfully."""
    duration = "PT8M14S"

    expected_seconds = int(timedelta(minutes=8, seconds=14).total_seconds())

    assert YoutubeScraper.parse_duration(duration) == expected_seconds


def test_youtube_very_long_duration_parsing():
    """Ensure a strange, extremely long YouTube duration parses successfully."""
    duration = "P30W2DT8H2M32S"

    expected_delta = timedelta(weeks=30, days=2, hours=8, minutes=2, seconds=32)
    expected_seconds = int(expected_delta.total_seconds())

    assert YoutubeScraper.parse_duration(duration) == expected_seconds


def test_youtube_duration_parsing_invalid():
    """Ensure an invalid duration raises a ValueError."""
    with raises(ValueError):
        YoutubeScraper.parse_duration("18:15")
