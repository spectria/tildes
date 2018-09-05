# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from marshmallow import Schema, ValidationError
from pytest import raises

from tildes.schemas.fields import Markdown


class MarkdownFieldTestSchema(Schema):
    """Simple schema class with a standard Markdown field."""

    markdown = Markdown()


def validate_string(string):
    """Validate a string against a standard Markdown field."""
    MarkdownFieldTestSchema(strict=True).validate({"markdown": string})


def test_normal_text_validates():
    """Ensure some "normal-looking" markdown validates."""
    validate_string(
        "Here's some markdown.\n\n"
        "It has **a bit of bold**, [a link](http://example.com)\n"
        "> And `some code` in a blockquote"
    )


def test_changing_max_length():
    """Ensure changing the max_length argument works."""
    test_string = "Just some text to try"

    # should normally validate
    assert Markdown()._validate(test_string) is None

    # but fails if you set a too-short max_length
    with raises(ValidationError):
        Markdown(max_length=len(test_string) - 1)._validate(test_string)


def test_extremely_long_string():
    """Ensure an extremely long string fails validation."""
    with raises(ValidationError):
        validate_string("A" * 100_000)


def test_empty_string():
    """Ensure an empty string fails validation."""
    with raises(ValidationError):
        validate_string("")


def test_all_whitespace_string():
    """Ensure a string that's all whitespace chars fails validation."""
    with raises(ValidationError):
        validate_string("  \n  \n\r\n  \t  ")


def test_carriage_returns_stripped():
    """Ensure loading a value strips out carriage returns from the string."""
    test_string = "some\r\nreturns\r\nin\nhere"

    schema = MarkdownFieldTestSchema(strict=True)
    result = schema.load({"markdown": test_string})

    assert "\r" not in result.data["markdown"]
