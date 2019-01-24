# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Validation schema for topic listing views."""

from marshmallow import pre_load, Schema, validates_schema, ValidationError
from marshmallow.fields import Boolean, Integer
from marshmallow.validate import Range

from tildes.enums import TopicSortOption
from tildes.schemas.fields import Enum, ID36, Ltree, PostType, ShortTimePeriod


class PaginatedListingSchema(Schema):
    """Marshmallow schema to validate arguments for a paginated listing page."""

    after = ID36()
    before = ID36()
    per_page = Integer(validate=Range(min=1, max=100), missing=50)

    @validates_schema
    def either_after_or_before(self, data: dict) -> None:
        """Fail validation if both after and before were specified."""
        if data.get("after") and data.get("before"):
            raise ValidationError("Can't specify both after and before.")

    class Meta:
        """Always use strict checking so error handlers are invoked."""

        strict = True


class TopicListingSchema(PaginatedListingSchema):
    """Marshmallow schema to validate arguments for a topic listing page."""

    period = ShortTimePeriod(allow_none=True)
    order = Enum(TopicSortOption)
    tag = Ltree(missing=None)
    unfiltered = Boolean(missing=False)
    rank_start = Integer(load_from="n", validate=Range(min=1), missing=None)

    @pre_load
    def reset_rank_start_on_first_page(self, data: dict) -> dict:
        """Reset rank_start to 1 if this is a first page (no before/after)."""
        if not (data.get("before") or data.get("after")):
            data["rank_start"] = 1

        return data


class MixedListingSchema(PaginatedListingSchema):
    """Marshmallow schema to validate arguments for a "mixed" listing page.

    By "mixed", this means that the listing can contain topics and/or comments, instead
    of just one or the other.
    """

    anchor_type = PostType()

    @pre_load
    def set_anchor_type_from_before_or_after(self, data: dict) -> dict:
        """Set the anchor_type if before or after has a special value indicating type.

        For example, if after or before looks like "t-123" that means it is referring
        to the topic with ID36 "123". "c-123" also works, for comments.
        """
        keys = ("after", "before")

        for key in keys:
            value = data.get(key)
            if not value:
                continue

            type_char, _, id36 = value.partition("-")
            if not id36:
                continue

            if type_char == "c":
                data["anchor_type"] = "comment"
            elif type_char == "t":
                data["anchor_type"] = "topic"
            else:
                continue

            data[key] = id36

        return data
