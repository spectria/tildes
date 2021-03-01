# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from marshmallow import ValidationError
from pytest import fixture, raises

from tildes.schemas.topic import TITLE_MAX_LENGTH, TopicSchema


@fixture
def title_schema():
    """Fixture for generating a title-only TopicSchema."""
    return TopicSchema(only=("title",))


def test_typical_title_valid(title_schema):
    """Test a "normal-looking" title to make sure it's valid."""
    title = "[Something] Here's an article that I'm sure 100 people will like."
    assert title_schema.validate({"title": title}) == {}


def test_too_long_title_invalid(title_schema):
    """Ensure a too-long title is invalid."""
    title = "x" * (TITLE_MAX_LENGTH + 1)
    with raises(ValidationError):
        title_schema.load({"title": title})


def test_empty_title_invalid(title_schema):
    """Ensure an empty title is invalid."""
    with raises(ValidationError):
        title_schema.load({"title": ""})


def test_whitespace_only_title_invalid(title_schema):
    """Ensure a whitespace-only title is invalid."""
    with raises(ValidationError):
        title_schema.load({"title": "    \n    "})


def test_whitespace_trimmed(title_schema):
    """Ensure leading/trailing whitespace on a title is removed."""
    title = "    actual title    "
    result = title_schema.load({"title": title})
    assert result["title"] == "actual title"


def test_trailing_periods_trimmed(title_schema):
    """Ensure trailing periods on a single-sentence title are removed."""
    title = "This is an interesting story."
    result = title_schema.load({"title": title})
    assert not result["title"].endswith(".")


def test_multisentence_trailing_period_kept(title_schema):
    """Ensure a trailing period is kept if the title has multiple sentences."""
    title = "I came. I saw. I conquered."
    result = title_schema.load({"title": title})
    assert result["title"].endswith(".")


def test_consecutive_whitespace_removed(title_schema):
    """Ensure consecutive whitespace in a title is compressed."""
    title = "sure   are  \n  a  lot    of     spaces"
    result = title_schema.load({"title": title})
    assert result["title"] == "sure are a lot of spaces"


def test_unicode_spaces_normalized(title_schema):
    """Test that some unicode space characters are converted to normal ones."""
    title = "some\u2009weird\u00a0spaces\u205fin\u00a0here"
    result = title_schema.load({"title": title})
    assert result["title"] == "some weird spaces in here"


def test_unicode_control_chars_removed(title_schema):
    """Test that some unicode control characters are stripped from titles."""
    title = "nothing\u0000strange\u0085going\u009con\u007fhere"
    result = title_schema.load({"title": title})
    assert result["title"] == "nothingstrangegoingonhere"


def test_zero_width_joiner_emojis_kept(title_schema):
    """Test that emojis are parsed correctly"""
    title = "🤷🤷‍♂️🤷‍♀️🤷🏻🤷🏻‍♀️🤷🏻‍♂️🤷🏼🤷🏼‍♀️🤷🏼‍♂️🤷🏽🤷🏽‍♀️🤷🏽‍♂️🤷🏾🤷🏾‍♀️🤷🏾‍♂️🤷🏿🤷🏿‍♀️🤷🏿‍♂️"
    result = title_schema.load({"title": title})
    assert (
        result["title"]
        == "🤷🤷‍♂️🤷‍♀️🤷🏻🤷🏻‍♀️🤷🏻‍♂️🤷🏼🤷🏼‍♀️🤷🏼‍♂️🤷🏽🤷🏽‍♀️🤷🏽‍♂️🤷🏾🤷🏾‍♀️🤷🏾‍♂️🤷🏿🤷🏿‍♀️🤷🏿‍♂️"
    )
