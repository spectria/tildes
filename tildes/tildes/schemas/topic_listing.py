"""Validation schema for topic listing views."""

from marshmallow import pre_load, Schema, validates_schema, ValidationError
from marshmallow.fields import Boolean, Integer
from marshmallow.validate import Range

from tildes.enums import TopicSortOption
from tildes.schemas.fields import Enum, ID36, Ltree, ShortTimePeriod


class TopicListingSchema(Schema):
    """Marshmallow schema to validate arguments for a topic listing page."""

    DEFAULT_TOPICS_PER_PAGE = 50

    order = Enum(TopicSortOption)
    period = ShortTimePeriod(allow_none=True)
    after = ID36()
    before = ID36()
    per_page = Integer(validate=Range(min=1, max=100), missing=DEFAULT_TOPICS_PER_PAGE)
    rank_start = Integer(load_from="n", validate=Range(min=1), missing=None)
    tag = Ltree(missing=None)
    unfiltered = Boolean(missing=False)

    @validates_schema
    def either_after_or_before(self, data: dict) -> None:
        """Fail validation if both after and before were specified."""
        if data.get("after") and data.get("before"):
            raise ValidationError("Can't specify both after and before.")

    @pre_load
    def reset_rank_start_on_first_page(self, data: dict) -> dict:
        """Reset rank_start to 1 if this is a first page (no before/after)."""
        if not (data.get("before") or data.get("after")):
            data["rank_start"] = 1

        return data

    class Meta:
        """Always use strict checking so error handlers are invoked."""

        strict = True
