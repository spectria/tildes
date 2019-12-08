# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Validation/dumping schema for comments."""

from marshmallow import Schema

from tildes.enums import CommentLabelOption
from tildes.schemas.fields import Enum, ID36, Markdown, SimpleString


class CommentSchema(Schema):
    """Marshmallow schema for comments."""

    comment_id36 = ID36()
    markdown = Markdown()
    parent_comment_id36 = ID36()


class CommentLabelSchema(Schema):
    """Marshmallow schema for comment labels."""

    name = Enum(CommentLabelOption)
    reason = SimpleString(max_length=1000, missing=None)
