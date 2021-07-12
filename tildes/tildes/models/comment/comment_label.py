# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the CommentLabel class."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, ForeignKey, REAL, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql.expression import text

from tildes.enums import CommentLabelOption
from tildes.metrics import incr_counter
from tildes.models import DatabaseModel
from tildes.models.user import User

from .comment import Comment


class CommentLabel(DatabaseModel):
    """Model for the labels attached to comments by users.

    Trigger behavior:
      Outgoing:
        - Inserting a row for an exemplary label will set last_exemplary_label_time for
          the relevant user.
    """

    __tablename__ = "comment_labels"

    comment_id: int = Column(
        BigInteger, ForeignKey("comments.comment_id"), nullable=False, primary_key=True
    )
    label: CommentLabelOption = Column(
        ENUM(CommentLabelOption), nullable=False, primary_key=True
    )
    user_id: int = Column(
        BigInteger, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    weight: float = Column(REAL, nullable=False, server_default=text("1.0"))
    reason: Optional[str] = Column(Text)

    comment: Comment = relationship(Comment, backref=backref("labels", lazy=False))
    user: User = relationship(User, lazy=False, innerjoin=True)

    def __init__(
        self,
        comment: Comment,
        user: User,
        label: CommentLabelOption,
        weight: float,
        reason: Optional[str] = None,
    ):
        """Add a new label to a comment."""
        self.comment = comment
        self.user = user
        self.label = label
        self.weight = weight
        self.reason = reason

    def _update_creation_metric(self) -> None:
        incr_counter("comment_labels", label=self.label.name)

    @property
    def name(self) -> str:
        """Return the name of the label (to avoid needing to do .label.name)."""
        return self.label.name.lower()
