# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from marshmallow import Schema, ValidationError
from pytest import raises

from tildes.schemas.fields import SimpleString


class SimpleStringTestSchema(Schema):
    """Simple schema class with a standard SimpleString field."""

    subject = SimpleString()


def process_string(string):
    """Deserialize a string with the field and return the "final" version.

    This also works for testing validation since .load() will raise a ValidationError if
    an invalid string is attempted.
    """
    schema = SimpleStringTestSchema(strict=True)
    result = schema.load({"subject": string})

    return result.data["subject"]


def test_changing_max_length():
    """Ensure changing the max_length argument works."""
    test_string = "Just some text to try"

    # should normally validate
    assert SimpleString()._validate(test_string) is None

    # but fails if you set a too-short max_length
    with raises(ValidationError):
        SimpleString(max_length=len(test_string) - 1)._validate(test_string)


def test_long_string():
    """Ensure a long string fails validation."""
    with raises(ValidationError):
        process_string("A" * 10000)


def test_empty_string():
    """Ensure an empty string fails validation."""
    with raises(ValidationError):
        process_string("")


def test_all_whitespace_string():
    """Ensure a string that's entirely whitespace fails validation."""
    with raises(ValidationError):
        process_string("\n  \t \r\n    ")


def test_normal_string_untouched():
    """Ensure a "normal" string comes through untouched."""
    original = "Here's a pretty normal string that might be a subject!"
    assert process_string(original) == original


def test_separator_chars_replaced():
    """Ensure "separator" chars other than spaces are replaced with spaces."""
    original = "I'm using\u2028chars\u2009that\u205fI\u00a0shouldn't\u2003be."
    result = process_string(original)

    assert result == "I'm using chars that I shouldn't be."


def test_control_chars_removed():
    """Ensure "control" chars get removed from the string."""
    original = "I can be \nsneaky and\t add \u200b\u200fproblem\u0000chars."
    result = process_string(original)

    assert result == "I can be sneaky and add problemchars."


def test_leading_trailing_spaces_removed():
    """Ensure leading/trailing spaces are removed from the string."""
    original = "          Centered!          "
    assert process_string(original) == "Centered!"


def test_consecutive_spaces_collapsed():
    """Ensure runs of consecutive spaces are "collapsed" inside the string."""
    original = "I    wanted   to      space    this        out"
    assert process_string(original) == "I wanted to space this out"
