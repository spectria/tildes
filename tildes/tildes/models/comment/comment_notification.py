"""Contains the CommentNotification class."""

from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tildes.enums import CommentNotificationType
from tildes.models import DatabaseModel
from tildes.models.user import User
from .comment import Comment


class CommentNotification(DatabaseModel):
    """Model for a notification created by a comment.

    Trigger behavior:
      Incoming:
        - Rows will be deleted if the relevant comment has is_deleted set to
          true.
      Outgoing:
        - Inserting, deleting, or updating is_unread will increment or
          decrement num_unread_notifications for the relevant user.
    """

    __tablename__ = 'comment_notifications'

    user_id: int = Column(
        Integer,
        ForeignKey('users.user_id'),
        nullable=False,
        primary_key=True,
    )
    comment_id: int = Column(
        Integer,
        ForeignKey('comments.comment_id'),
        nullable=False,
        primary_key=True,
    )
    notification_type: CommentNotificationType = Column(
        ENUM(CommentNotificationType), nullable=False)
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('NOW()'),
    )
    is_unread: bool = Column(
        Boolean, nullable=False, server_default='true', index=True)

    user: User = relationship('User', innerjoin=True)
    comment: Comment = relationship('Comment', innerjoin=True)

    def __init__(
            self,
            user: User,
            comment: Comment,
            notification_type: CommentNotificationType,
    ) -> None:
        """Create a new notification for a user from a comment."""
        self.user = user
        self.comment = comment
        self.notification_type = notification_type

    @property
    def is_comment_reply(self) -> bool:
        """Return whether this is a comment reply notification."""
        return self.notification_type == CommentNotificationType.COMMENT_REPLY

    @property
    def is_topic_reply(self) -> bool:
        """Return whether this is a topic reply notification."""
        return self.notification_type == CommentNotificationType.TOPIC_REPLY
