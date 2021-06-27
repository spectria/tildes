# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the TopicVisit class."""

from datetime import datetime

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tildes.models import DatabaseModel
from tildes.models.user import User

from .topic import Topic


class TopicVisit(DatabaseModel):
    """Model for a user's visits to a topic.

    Trigger behavior:
      Incoming:
        - num_comments will be incremented for the author's topic visit when they post a
          comment in that topic.
        - num_comments will be decremented when a comment is deleted, for all visits to
          the topic that were after it was posted.
    """

    __tablename__ = "topic_visits"

    user_id: int = Column(
        BigInteger, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    topic_id: int = Column(
        BigInteger, ForeignKey("topics.topic_id"), nullable=False, primary_key=True
    )
    visit_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        primary_key=True,
        server_default=text("NOW()"),
    )
    num_comments: int = Column(Integer, nullable=False)

    user: User = relationship("User", innerjoin=True)
    topic: Topic = relationship("Topic", innerjoin=True)

    def __init__(self, user: User, topic: Topic):
        """Create a new visit to a topic."""
        self.user = user
        self.topic = topic
        self.num_comments = topic.num_comments
