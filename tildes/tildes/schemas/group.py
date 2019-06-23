# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Validation/dumping schema for groups."""

import re

import sqlalchemy_utils
from marshmallow import pre_load, Schema, validates
from marshmallow.exceptions import ValidationError
from marshmallow.fields import DateTime

from tildes.schemas.fields import Ltree, Markdown, SimpleString


# Validation regex for each individual "element" of a group path, encodes:
#   - must start with a number or lowercase letter
#   - must end with a number or lowercase letter
#   - the middle can contain numbers, lowercase letters, and underscores
# Note: this regex does not contain any length checks, must be done separately
# fmt: off
GROUP_PATH_ELEMENT_VALID_REGEX = re.compile(
    "^[a-z0-9]"  # start
    "([a-z0-9_]*"  # middle
    "[a-z0-9])?$"  # end
)
# fmt: on

SHORT_DESCRIPTION_MAX_LENGTH = 200


class GroupSchema(Schema):
    """Marshmallow schema for groups."""

    path = Ltree(required=True, load_from="group_path")
    created_time = DateTime(dump_only=True)
    short_description = SimpleString(
        max_length=SHORT_DESCRIPTION_MAX_LENGTH, allow_none=True
    )
    sidebar_markdown = Markdown(allow_none=True)

    @pre_load
    def prepare_path(self, data: dict) -> dict:
        """Prepare the path value before it's validated."""
        if not self.context.get("fix_path_capitalization"):
            return data

        # path can also be loaded from group_path, so we need to check both
        keys = ("path", "group_path")

        for key in keys:
            if key in data and isinstance(data[key], str):
                data[key] = data[key].lower()

        return data

    @validates("path")
    def validate_path(self, value: sqlalchemy_utils.Ltree) -> None:
        """Validate the path field, raising an error if an issue exists."""
        # check each element for length and against validity regex
        path_elements = value.path.split(".")
        for element in path_elements:
            if len(element) > 256:
                raise ValidationError("Path element %s is too long" % element)

            if not GROUP_PATH_ELEMENT_VALID_REGEX.match(element):
                raise ValidationError("Path element %s is invalid" % element)

    @pre_load
    def prepare_sidebar_markdown(self, data: dict) -> dict:
        """Prepare the sidebar_markdown value before it's validated."""
        if "sidebar_markdown" not in data:
            return data

        # if the value is empty, convert it to None
        if not data["sidebar_markdown"] or data["sidebar_markdown"].isspace():
            data["sidebar_markdown"] = None

        return data

    class Meta:
        """Always use strict checking so error handlers are invoked."""

        strict = True


def is_valid_group_path(path: str) -> bool:
    """Return whether the group path is valid or not."""
    schema = GroupSchema(partial=True)
    try:
        schema.validate({"path": path})
    except ValidationError:
        return False

    return True
