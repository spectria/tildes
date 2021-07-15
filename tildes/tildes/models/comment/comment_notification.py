# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the CommentNotification class."""

import re
from datetime import datetime

from pyramid.security import Allow, DENY_ALL
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql.expression import text

from tildes.enums import CommentNotificationType
from tildes.lib.markdown import LinkifyFilter
from tildes.models import DatabaseModel
from tildes.models.topic import TopicIgnore
from tildes.models.user import User
from tildes.typing import AclType

from .comment import Comment


class CommentNotification(DatabaseModel):
    """Model for a notification created by a comment.

    Trigger behavior:
      Incoming:
        - Rows will be deleted if the relevant comment has is_deleted set to true.
      Outgoing:
        - Inserting, deleting, or updating is_unread will increment or decrement
          num_unread_notifications for the relevant user.
    """

    __tablename__ = "comment_notifications"

    user_id: int = Column(
        BigInteger, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    comment_id: int = Column(
        BigInteger, ForeignKey("comments.comment_id"), nullable=False, primary_key=True
    )
    notification_type: CommentNotificationType = Column(
        ENUM(CommentNotificationType), nullable=False
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    is_unread: bool = Column(Boolean, nullable=False, server_default="true", index=True)

    user: User = relationship("User", innerjoin=True)
    comment: Comment = relationship("Comment", innerjoin=True)

    def __init__(
        self, user: User, comment: Comment, notification_type: CommentNotificationType
    ):
        """Create a new notification for a user from a comment."""
        if (
            notification_type
            in (
                CommentNotificationType.COMMENT_REPLY,
                CommentNotificationType.TOPIC_REPLY,
            )
            and not self.should_create_reply_notification(comment)
        ):
            raise ValueError("That comment shouldn't create a reply notification")

        self.user = user
        self.comment = comment
        self.notification_type = notification_type

    def __acl__(self) -> AclType:
        """Pyramid security ACL."""
        acl = []
        acl.append((Allow, self.user_id, "mark_read"))
        acl.append(DENY_ALL)
        return acl

    @classmethod
    def should_create_reply_notification(cls, comment: Comment) -> bool:
        """Return whether a comment should generate a reply notification."""
        # User is replying to their own post
        if comment.parent.user == comment.user:
            return False

        if not comment.parent.user.is_real_user:
            return False

        # check if the parent's author is ignoring the topic
        if (
            Session.object_session(comment)
            .query(TopicIgnore)
            .filter(
                TopicIgnore.user == comment.parent.user,
                TopicIgnore.topic == comment.topic,
            )
            .one_or_none()
        ):
            return False

        return True

    @property
    def is_comment_reply(self) -> bool:
        """Return whether this is a comment reply notification."""
        return self.notification_type == CommentNotificationType.COMMENT_REPLY

    @property
    def is_topic_reply(self) -> bool:
        """Return whether this is a topic reply notification."""
        return self.notification_type == CommentNotificationType.TOPIC_REPLY

    @property
    def is_mention(self) -> bool:
        """Return whether this is a mention notification."""
        return self.notification_type == CommentNotificationType.USER_MENTION

    @classmethod
    def get_mentions_for_comment(
        cls, db_session: Session, comment: Comment
    ) -> list["CommentNotification"]:
        """Get a list of notifications for user mentions in the comment."""
        notifications = []

        raw_names = re.findall(LinkifyFilter.USERNAME_REFERENCE_REGEX, comment.markdown)
        users_to_mention = (
            db_session.query(User)
            .filter(User.username.in_(raw_names))  # type: ignore
            .all()
        )

        for user in users_to_mention:
            # prevent the user from mentioning themselves
            if comment.user == user:
                continue

            # prevent mentioning the user they're replying to
            # (they'll already get a reply notification)
            if comment.parent.user == user:
                continue

            # prevent mentioning users ignoring the topic
            if (
                db_session.query(TopicIgnore)
                .filter(TopicIgnore.user == user, TopicIgnore.topic == comment.topic)
                .one_or_none()
            ):
                continue

            mention_notification = cls(
                user, comment, CommentNotificationType.USER_MENTION
            )
            notifications.append(mention_notification)

        return notifications

    @staticmethod
    def prevent_duplicate_notifications(
        db_session: Session,
        comment: Comment,
        new_notifications: list["CommentNotification"],
    ) -> tuple[list["CommentNotification"], list["CommentNotification"]]:
        """Filter new notifications for edited comments.

        Protect against sending a notification for the same comment to the same user
        twice. Edits can sent notifications to users now mentioned in the content, but
        only if they weren't sent a notification for that comment before.

        This method returns a tuple of lists of this class. The first item is the
        notifications that were previously sent for this comment but need to be deleted
        (i.e. mentioned username was edited out of the comment), and the second item is
        the notifications that need to be added, as they're new.
        """
        previous_notifications = (
            db_session.query(CommentNotification)
            .filter(
                CommentNotification.comment_id == comment.comment_id,
                CommentNotification.notification_type
                == CommentNotificationType.USER_MENTION,
            )
            .all()
        )

        new_mention_user_ids = [
            notification.user.user_id for notification in new_notifications
        ]

        previous_mention_user_ids = [
            notification.user_id for notification in previous_notifications
        ]

        to_delete = [
            notification
            for notification in previous_notifications
            if notification.user.user_id not in new_mention_user_ids
        ]

        to_add = [
            notification
            for notification in new_notifications
            if notification.user.user_id not in previous_mention_user_ids
        ]

        return (to_delete, to_add)
