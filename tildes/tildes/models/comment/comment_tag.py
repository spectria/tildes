# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the CommentTag class."""

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql.expression import text

from tildes.enums import CommentTagOption
from tildes.models import DatabaseModel
from tildes.models.user import User
from .comment import Comment


class CommentTag(DatabaseModel):
    """Model for the tags attached to comments by users."""

    __tablename__ = "comment_tags"

    comment_id: int = Column(
        Integer, ForeignKey("comments.comment_id"), nullable=False, primary_key=True
    )
    tag: CommentTagOption = Column(
        ENUM(CommentTagOption), nullable=False, primary_key=True
    )
    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )

    comment: Comment = relationship(Comment, backref=backref("tags", lazy=False))

    def __init__(self, comment: Comment, user: User, tag: CommentTagOption) -> None:
        """Add a new tag to a comment."""
        self.comment_id = comment.comment_id
        self.user_id = user.user_id
        self.tag = tag

    @property
    def name(self) -> str:
        """Return the name of the tag (to avoid needing to do .tag.name)."""
        return self.tag.name.lower()
