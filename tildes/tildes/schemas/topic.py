# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Validation/dumping schema for topics."""

import re
import typing
from typing import Any
from urllib.parse import urlparse

from marshmallow import pre_load, Schema, validates, validates_schema, ValidationError
from marshmallow.fields import DateTime, List, Nested, String, URL

from tildes.lib.url_transform import apply_url_transformations
from tildes.schemas.fields import Enum, ID36, Markdown, SimpleString
from tildes.schemas.group import GroupSchema
from tildes.schemas.user import UserSchema


TITLE_MAX_LENGTH = 200
TAG_SYNONYMS = {"spoiler": ["spoilers"]}


class TopicSchema(Schema):
    """Marshmallow schema for topics."""

    topic_id36 = ID36()
    title = SimpleString(max_length=TITLE_MAX_LENGTH)
    topic_type = Enum(dump_only=True)
    markdown = Markdown(allow_none=True)
    rendered_html = String(dump_only=True)
    link = URL(schemes={"http", "https"}, allow_none=True)
    created_time = DateTime(dump_only=True)
    tags = List(String())

    user = Nested(UserSchema, dump_only=True)
    group = Nested(GroupSchema, dump_only=True)

    @pre_load
    def prepare_tags(self, data: dict, many: bool, partial: Any) -> dict:
        """Prepare the tags before they're validated."""
        # pylint: disable=unused-argument
        if "tags" not in data:
            return data

        tags: typing.List[str] = []

        for tag in data["tags"]:
            tag = tag.lower()

            # replace underscores with spaces
            tag = tag.replace("_", " ")

            # remove any consecutive spaces
            tag = re.sub(" {2,}", " ", tag)

            # remove any leading/trailing spaces
            tag = tag.strip(" ")

            # drop any empty tags
            if not tag or tag.isspace():
                continue

            # handle synonyms
            for name, synonyms in TAG_SYNONYMS.items():
                if tag in synonyms:
                    tag = name

            # skip any duplicate tags
            if tag in tags:
                continue

            tags.append(tag)

        data["tags"] = tags

        return data

    @validates("tags")
    def validate_tags(self, value: typing.List[str]) -> None:
        """Validate the tags field, raising an error if an issue exists.

        Note that tags are validated by ensuring that each tag would be a valid group
        path. This is definitely mixing concerns, but it's deliberate in this case. It
        will allow for some interesting possibilities by ensuring naming "compatibility"
        between groups and tags. For example, a popular tag in a group could be
        converted into a sub-group easily.
        """
        group_schema = GroupSchema(partial=True)
        for tag in value:
            try:
                group_schema.load({"path": tag})
            except ValidationError:
                raise ValidationError("Tag %s is invalid" % tag)

    @pre_load
    def prepare_markdown(self, data: dict, many: bool, partial: Any) -> dict:
        """Prepare the markdown value before it's validated."""
        # pylint: disable=unused-argument
        if "markdown" not in data:
            return data

        # if the value is empty, convert it to None
        if not data["markdown"] or data["markdown"].isspace():
            data["markdown"] = None

        return data

    @pre_load
    def prepare_link(self, data: dict, many: bool, partial: Any) -> dict:
        """Prepare the link value before it's validated."""
        # pylint: disable=unused-argument
        if "link" not in data:
            return data

        # if the value is empty, convert it to None
        if not data["link"] or data["link"].isspace():
            data["link"] = None
            return data

        # prepend http:// to the link if it doesn't have a scheme
        parsed = urlparse(data["link"])
        if not parsed.scheme:
            data["link"] = "http://" + data["link"]

        # run the link through the url-transformation process
        data["link"] = apply_url_transformations(data["link"])

        return data

    @validates_schema
    def link_or_markdown(self, data: dict, many: bool, partial: Any) -> None:
        """Fail validation unless at least one of link or markdown were set."""
        # pylint: disable=unused-argument
        if "link" not in data and "markdown" not in data:
            return

        link = data.get("link")
        markdown = data.get("markdown")

        if not (markdown or link):
            raise ValidationError("Topics must have either markdown or a link.")
