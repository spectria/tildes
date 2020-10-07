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
    def prepare_title(self, data: dict, many: bool, partial: Any) -> dict:
        """Prepare the title before it's validated."""
        # pylint: disable=unused-argument
        if "title" not in data:
            return data

        new_data = data.copy()

        split_title = re.split("[.?!]+", new_data["title"])

        # the last string in the list will be empty if it ended with punctuation
        num_sentences = len([piece for piece in split_title if piece])

        # strip trailing periods off single-sentence titles
        if num_sentences == 1:
            new_data["title"] = new_data["title"].rstrip(".")

        return new_data

    @pre_load
    def prepare_tags(self, data: dict, many: bool, partial: Any) -> dict:
        """Prepare the tags before they're validated."""
        # pylint: disable=unused-argument
        if "tags" not in data:
            return data

        new_data = data.copy()

        tags: typing.List[str] = []

        for tag in new_data["tags"]:
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

        new_data["tags"] = tags

        return new_data

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

        new_data = data.copy()

        # if the value is empty, convert it to None
        if not new_data["markdown"] or new_data["markdown"].isspace():
            new_data["markdown"] = None

        return new_data

    @pre_load
    def prepare_link(self, data: dict, many: bool, partial: Any) -> dict:
        """Prepare the link value before it's validated."""
        # pylint: disable=unused-argument
        if "link" not in data:
            return data

        new_data = data.copy()

        # remove leading/trailing whitespace
        new_data["link"] = new_data["link"].strip()

        # if the value is empty, convert it to None
        if not new_data["link"]:
            new_data["link"] = None
            return new_data

        # prepend http:// to the link if it doesn't have a scheme
        parsed = urlparse(new_data["link"])
        if not parsed.scheme:
            new_data["link"] = "http://" + new_data["link"]

        # run the link through the url-transformation process
        new_data["link"] = apply_url_transformations(new_data["link"])

        return new_data

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
