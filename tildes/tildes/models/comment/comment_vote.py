# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the CommentVote class."""

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tildes.metrics import incr_counter
from tildes.models import DatabaseModel
from tildes.models.user import User

from .comment import Comment


class CommentVote(DatabaseModel):
    """Model for a user's vote on a comment.

    Trigger behavior:
      Outgoing:
        - Inserting or deleting a row will increment or decrement the num_votes column
          for the relevant comment.
    """

    __tablename__ = "comment_votes"

    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    comment_id: int = Column(
        Integer, ForeignKey("comments.comment_id"), nullable=False, primary_key=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )

    user: User = relationship("User", innerjoin=True)
    comment: Comment = relationship("Comment", innerjoin=True)

    def __init__(self, user: User, comment: Comment):
        """Create a new vote on a comment."""
        self.user = user
        self.comment = comment

        incr_counter("votes", target_type="comment")
