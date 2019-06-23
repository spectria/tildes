# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Custom schema field definitions."""

import enum
from typing import Any, Optional, Type

import sqlalchemy_utils
from marshmallow.exceptions import ValidationError
from marshmallow.fields import Field, String
from marshmallow.validate import Length, OneOf, Regexp

from tildes.lib.datetime import SimpleHoursPeriod
from tildes.lib.id import ID36_REGEX
from tildes.lib.string import simplify_string


class Enum(Field):
    """Field for a native Python Enum (or subclasses)."""

    def __init__(self, enum_class: Optional[Type] = None, *args: Any, **kwargs: Any):
        """Initialize the field with an optional enum class."""
        # pylint: disable=keyword-arg-before-vararg
        super().__init__(*args, **kwargs)
        self._enum_class = enum_class

    def _serialize(self, value: enum.Enum, attr: str, obj: object) -> str:
        """Serialize the enum value - lowercase version of its name."""
        return value.name.lower()

    def _deserialize(self, value: str, attr: str, data: dict) -> enum.Enum:
        """Deserialize a string to the enum member with that name."""
        if not self._enum_class:
            raise ValidationError("Cannot deserialize with no enum class.")

        try:
            return self._enum_class[value.upper()]
        except KeyError:
            raise ValidationError("Invalid enum member")


class ID36(String):
    """Field for a base-36 ID."""

    def __init__(self) -> None:
        """Initialize the field with a regex validator."""
        super().__init__(validate=Regexp(ID36_REGEX))


class ShortTimePeriod(Field):
    """Field for short time period strings like "4h" and "2d".

    Also supports the string "all" which will be converted to None.
    """

    def _deserialize(
        self, value: str, attr: str, data: dict
    ) -> Optional[SimpleHoursPeriod]:
        """Deserialize to a SimpleHoursPeriod object."""
        if value == "all":
            return None

        try:
            return SimpleHoursPeriod.from_short_form(value)
        except ValueError:
            raise ValidationError("Invalid time period")

    def _serialize(
        self, value: Optional[SimpleHoursPeriod], attr: str, obj: object
    ) -> Optional[str]:
        """Serialize the value to the "short form" string."""
        if not value:
            return None

        return value.as_short_form()


class Markdown(Field):
    """Field for markdown strings (comments, text topic, messages, etc.)."""

    DEFAULT_MAX_LENGTH = 50000

    def __init__(self, max_length: Optional[int] = None, **kwargs: Any):
        """Initialize the field with a length validator."""
        if not max_length:
            max_length = self.DEFAULT_MAX_LENGTH

        super().__init__(validate=Length(min=1, max=max_length), **kwargs)

    def _validate(self, value: str) -> None:
        """Validate the value is acceptable for a markdown field."""
        super()._validate(value)

        if value.isspace():
            raise ValidationError("Cannot be entirely whitespace.")

    def _deserialize(self, value: str, attr: str, data: dict) -> str:
        """Deserialize the string, removing carriage returns in the process."""
        value = value.replace("\r", "")

        return value

    def _serialize(self, value: str, attr: str, obj: object) -> str:
        """Serialize the value (no-op in this case)."""
        return value


class SimpleString(Field):
    """Field for "simple" strings, suitable for uses like subject, title, etc.

    These strings should generally not contain any special formatting (such as
    markdown), and have problematic whitespace/unicode/etc. removed.

    See the simplify_string() function for full details of how these strings are
    processed and sanitized.

    """

    DEFAULT_MAX_LENGTH = 200

    def __init__(self, max_length: Optional[int] = None, **kwargs: Any):
        """Initialize the field with a length validator."""
        if not max_length:
            max_length = self.DEFAULT_MAX_LENGTH

        super().__init__(validate=Length(min=1, max=max_length), **kwargs)

    def _deserialize(self, value: str, attr: str, data: dict) -> str:
        """Deserialize the string, removing/replacing as necessary."""
        return simplify_string(value)

    def _serialize(self, value: str, attr: str, obj: object) -> str:
        """Serialize the value (no-op in this case)."""
        return value


class Ltree(Field):
    """Field for postgresql ltree type."""

    def _serialize(self, value: sqlalchemy_utils.Ltree, attr: str, obj: object) -> str:
        """Serialize the Ltree value - use the (string) path."""
        return value.path

    def _deserialize(self, value: str, attr: str, data: dict) -> sqlalchemy_utils.Ltree:
        """Deserialize a string path to an Ltree object."""
        # convert to lowercase and replace spaces with underscores
        value = value.lower().replace(" ", "_")

        try:
            return sqlalchemy_utils.Ltree(value)
        except (TypeError, ValueError):
            raise ValidationError("Invalid path")


class PostType(String):
    """Field for selecting a type of post (topic or comment)."""

    def __init__(self, **kwargs: Any):
        """Initialize the field with a "one of" validator."""
        super().__init__(validate=OneOf(("topic", "comment")), **kwargs)
