# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Validation/dumping schema for users."""

import re

from marshmallow import post_dump, pre_load, Schema, validates, validates_schema
from marshmallow.exceptions import ValidationError
from marshmallow.fields import Boolean, DateTime, Email, String
from marshmallow.validate import Length, Regexp

from tildes.lib.password import is_breached_password
from tildes.schemas.fields import Markdown


USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 20

# Valid username regex, encodes the following:
#   - must start with a number or letter
#   - must end with a number or letter
#   - the middle can contain numbers, letters, underscores and dashes, but no more than
#     one underscore/dash consecutively (this includes both "_-" and "-_" sequences
#     being invalid)
# Note: this regex does not contain any length checks, must be done separately
# fmt: off
USERNAME_VALID_REGEX = re.compile(
    "^[a-z0-9]"  # start
    "([a-z0-9]|[_-](?![_-]))*"  # middle
    "[a-z0-9]$",  # end
    re.IGNORECASE,
)
# fmt: on

PASSWORD_MIN_LENGTH = 8

EMAIL_ADDRESS_NOTE_MAX_LENGTH = 100

BIO_MAX_LENGTH = 2000


class UserSchema(Schema):
    """Marshmallow schema for users."""

    username = String(
        validate=(
            Length(min=USERNAME_MIN_LENGTH, max=USERNAME_MAX_LENGTH),
            Regexp(USERNAME_VALID_REGEX),
        ),
        required=True,
    )
    password = String(
        validate=Length(min=PASSWORD_MIN_LENGTH), required=True, load_only=True
    )
    email_address = Email(allow_none=True, load_only=True)
    email_address_note = String(validate=Length(max=EMAIL_ADDRESS_NOTE_MAX_LENGTH))
    created_time = DateTime(dump_only=True)
    track_comment_visits = Boolean()
    bio_markdown = Markdown(max_length=BIO_MAX_LENGTH, allow_none=True)

    @post_dump
    def anonymize_username(self, data: dict) -> dict:
        """Hide the username if the dumping context specifies to do so."""
        if "username" in data and self.context.get("hide_username"):
            data["username"] = "<unknown>"

        return data

    @validates_schema
    def username_pass_not_substrings(self, data: dict) -> None:
        """Ensure the username isn't in the password and vice versa."""
        username = data.get("username")
        password = data.get("password")
        if not (username and password):
            return

        username = username.lower()
        password = password.lower()

        if username in password:
            raise ValidationError("Password cannot contain username")

        if password in username:
            raise ValidationError("Username cannot contain password")

    @validates("password")
    def password_not_breached(self, value: str) -> None:
        """Validate that the password is not in the breached-passwords list.

        Requires check_breached_passwords be True in the schema's context.
        """
        if not self.context.get("check_breached_passwords"):
            return

        if is_breached_password(value):
            raise ValidationError("That password exists in a data breach (see sidebar)")

    @pre_load
    def username_trim_whitespace(self, data: dict) -> dict:
        """Trim leading/trailing whitespace around the username.

        Requires username_trim_whitespace be True in the schema's context.
        """
        if not self.context.get("username_trim_whitespace"):
            return data

        if "username" not in data:
            return data

        data["username"] = data["username"].strip()

        return data

    @pre_load
    def prepare_email_address(self, data: dict) -> dict:
        """Prepare the email address value before it's validated."""
        if "email_address" not in data:
            return data

        # remove any leading/trailing whitespace
        data["email_address"] = data["email_address"].strip()

        # if the value is empty, convert it to None
        if not data["email_address"] or data["email_address"].isspace():
            data["email_address"] = None

        return data

    @pre_load
    def prepare_bio_markdown(self, data: dict) -> dict:
        """Prepare the bio_markdown value before it's validated."""
        if "bio_markdown" not in data:
            return data

        # if the value is empty, convert it to None
        if not data["bio_markdown"] or data["bio_markdown"].isspace():
            data["bio_markdown"] = None

        return data

    class Meta:
        """Always use strict checking so error handlers are invoked."""

        strict = True


def is_valid_username(username: str) -> bool:
    """Return whether the username is valid or not.

    Simple convenience wrapper that uses the schema to validate a username, useful in
    cases where a simple valid/invalid result is needed without worrying about the
    specific reason for invalidity.
    """
    schema = UserSchema(partial=True)
    try:
        schema.validate({"username": username})
    except ValidationError:
        return False

    return True
