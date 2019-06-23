# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the TopicVisit class."""

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.dialects.postgresql.dml import Insert
from sqlalchemy.orm import relationship

from tildes.lib.datetime import utc_now
from tildes.models import DatabaseModel
from tildes.models.user import User

from .topic import Topic


class TopicVisit(DatabaseModel):
    """Model for a user's visit to a topic.

    New visits should not be created through __init__(), but by executing the statement
    returned by the `generate_insert_statement` method. This will take advantage of
    postgresql's ability to update any existing visit.

    Trigger behavior:
      Incoming:
        - num_comments will be incremented for the author's topic visit when they post a
          comment in that topic.
        - num_comments will be decremented when a comment is deleted, for all visits to
          the topic that were after it was posted.
    """

    __tablename__ = "topic_visits"

    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    topic_id: int = Column(
        Integer, ForeignKey("topics.topic_id"), nullable=False, primary_key=True
    )
    visit_time: datetime = Column(TIMESTAMP(timezone=True), nullable=False)
    num_comments: int = Column(Integer, nullable=False)

    user: User = relationship("User", innerjoin=True)
    topic: Topic = relationship("Topic", innerjoin=True)

    @classmethod
    def generate_insert_statement(cls, user: User, topic: Topic) -> Insert:
        """Return a INSERT ... ON CONFLICT DO UPDATE statement for a visit."""
        visit_time = utc_now()
        return (
            insert(cls.__table__)
            .values(
                user_id=user.user_id,
                topic_id=topic.topic_id,
                visit_time=visit_time,
                num_comments=topic.num_comments,
            )
            .on_conflict_do_update(
                constraint=cls.__table__.primary_key,
                set_={"visit_time": visit_time, "num_comments": topic.num_comments},
            )
        )
