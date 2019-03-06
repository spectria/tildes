"""Contains the TopicIgnore class."""

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tildes.models import DatabaseModel
from tildes.models.topic import Topic
from tildes.models.user import User


class TopicIgnore(DatabaseModel):
    """Model for an ignored topic."""

    __tablename__ = "topic_ignores"

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

    def __init__(self, user: User, topic: Topic) -> None:
        """Ignore a topic."""
        self.user = user
        self.topic = topic
