# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the TopicVote class."""

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tildes.metrics import incr_counter
from tildes.models import DatabaseModel
from tildes.models.user import User

from .topic import Topic


class TopicVote(DatabaseModel):
    """Model for a user's vote on a topic.

    Trigger behavior:
      Outgoing:
        - Inserting or deleting a row will increment or decrement the num_votes column
          for the relevant topic.
    """

    __tablename__ = "topic_votes"

    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    topic_id: int = Column(
        Integer, ForeignKey("topics.topic_id"), nullable=False, primary_key=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )

    user: User = relationship("User", innerjoin=True)
    topic: Topic = relationship("Topic", innerjoin=True)

    def __init__(self, user: User, topic: Topic):
        """Create a new vote on a topic."""
        self.user = user
        self.topic = topic

        incr_counter("votes", target_type="topic")
