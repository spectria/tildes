# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Validation/dumping schema for groups."""

import re
from typing import Any

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

    path = Ltree(required=True)
    created_time = DateTime(dump_only=True)
    short_description = SimpleString(
        max_length=SHORT_DESCRIPTION_MAX_LENGTH, allow_none=True
    )
    sidebar_markdown = Markdown(allow_none=True)

    @pre_load
    def prepare_path(self, data: dict, many: bool, partial: Any) -> dict:
        """Prepare the path value before it's validated."""
        # pylint: disable=unused-argument
        if not self.context.get("fix_path_capitalization"):
            return data

        if "path" in data and isinstance(data["path"], str):
            data["path"] = data["path"].lower()

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
    def prepare_sidebar_markdown(self, data: dict, many: bool, partial: Any) -> dict:
        """Prepare the sidebar_markdown value before it's validated."""
        # pylint: disable=unused-argument
        if "sidebar_markdown" not in data:
            return data

        # if the value is empty, convert it to None
        if not data["sidebar_markdown"] or data["sidebar_markdown"].isspace():
            data["sidebar_markdown"] = None

        return data


def is_valid_group_path(path: str) -> bool:
    """Return whether the group path is valid or not."""
    schema = GroupSchema(partial=True)
    errors = schema.validate({"path": path})
    return not errors
