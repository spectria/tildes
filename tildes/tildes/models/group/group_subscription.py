# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the GroupSubscription class."""

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tildes.metrics import incr_counter
from tildes.models import DatabaseModel
from tildes.models.user import User

from .group import Group


class GroupSubscription(DatabaseModel):
    """Model for a user's subscription to a group.

    Trigger behavior:
      Outgoing:
        - Inserting or deleting a row will increment or decrement the num_subscriptions
          column for the relevant group.
    """

    __tablename__ = "group_subscriptions"

    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    group_id: int = Column(
        Integer, ForeignKey("groups.group_id"), nullable=False, primary_key=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )

    user: User = relationship("User", innerjoin=True, backref="subscriptions")
    group: Group = relationship("Group", innerjoin=True, lazy=False)

    def __init__(self, user: User, group: Group):
        """Create a new subscription to a group."""
        self.user = user
        self.group = group

        incr_counter("subscriptions")
