"""Validation/dumping schema for comments."""

from marshmallow import Schema

from tildes.enums import CommentTagOption
from tildes.schemas.fields import Enum, ID36, Markdown


class CommentSchema(Schema):
    """Marshmallow schema for comments."""

    markdown = Markdown()
    parent_comment_id36 = ID36()

    class Meta:
        """Always use strict checking so error handlers are invoked."""

        strict = True


class CommentTagSchema(Schema):
    """Marshmallow schema for comment tags."""

    name = Enum(CommentTagOption)

    class Meta:
        """Always use strict checking so error handlers are invoked."""

        strict = True
