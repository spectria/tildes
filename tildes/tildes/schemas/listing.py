# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Validation schema for topic listing views."""

from typing import Any

from marshmallow import pre_load, Schema, validates_schema, ValidationError
from marshmallow.fields import Boolean, Integer
from marshmallow.validate import Range

from tildes.enums import TopicSortOption
from tildes.schemas.fields import Enum, ID36, Ltree, PostType, ShortTimePeriod


class PaginatedListingSchema(Schema):
    """Marshmallow schema to validate arguments for a paginated listing page."""

    after = ID36(missing=None)
    before = ID36(missing=None)
    per_page = Integer(validate=Range(min=1, max=100), missing=50)

    @validates_schema
    def either_after_or_before(self, data: dict, many: bool, partial: Any) -> None:
        """Fail validation if both after and before were specified."""
        # pylint: disable=unused-argument
        if data.get("after") and data.get("before"):
            raise ValidationError("Can't specify both after and before.")


class TopicListingSchema(PaginatedListingSchema):
    """Marshmallow schema to validate arguments for a topic listing page."""

    period = ShortTimePeriod(allow_none=True)
    order = Enum(TopicSortOption, missing=None)
    tag = Ltree(missing=None)
    unfiltered = Boolean(missing=False)
    rank_start = Integer(data_key="n", validate=Range(min=1), missing=None)

    @pre_load
    def reset_rank_start_on_first_page(
        self, data: dict, many: bool, partial: Any
    ) -> dict:
        """Reset rank_start to 1 if this is a first page (no before/after)."""
        # pylint: disable=unused-argument
        if "rank_start" not in self.fields:
            return data

        new_data = data.copy()

        if not (new_data.get("before") or new_data.get("after")):
            new_data["n"] = 1

        return new_data


class MixedListingSchema(PaginatedListingSchema):
    """Marshmallow schema to validate arguments for a "mixed" listing page.

    By "mixed", this means that the listing can contain topics and/or comments, instead
    of just one or the other.
    """

    anchor_type = PostType(missing=None)

    @pre_load
    def set_anchor_type_from_before_or_after(
        self, data: dict, many: bool, partial: Any
    ) -> dict:
        """Set the anchor_type if before or after has a special value indicating type.

        For example, if after or before looks like "t-123" that means it is referring
        to the topic with ID36 "123". "c-123" also works, for comments.
        """
        # pylint: disable=unused-argument
        new_data = data.copy()

        keys = ("after", "before")

        for key in keys:
            value = new_data.get(key)
            if not value:
                continue

            type_char, _, id36 = value.partition("-")
            if not id36:
                continue

            if type_char == "c":
                new_data["anchor_type"] = "comment"
            elif type_char == "t":
                new_data["anchor_type"] = "topic"
            else:
                continue

            new_data[key] = id36

        return new_data
