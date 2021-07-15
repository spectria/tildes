# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the MessageConversation and MessageReply classes.

Note the difference between these two classes - MessageConversation represents both the
overall conversation and the initial message in a particular message
conversation/thread. Subsequent replies (if any) inside that same conversation are
represented by MessageReply.

This might feel a bit unusual since it splits "all messages" across two tables/classes,
but it simplifies a lot of things when organizing them into threads.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from pyramid.security import Allow, DENY_ALL
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import deferred, relationship
from sqlalchemy.sql.expression import text

from tildes.lib.id import id_to_id36
from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.metrics import incr_counter
from tildes.models import DatabaseModel
from tildes.models.user import User
from tildes.schemas.message import (
    MessageConversationSchema,
    MessageReplySchema,
    SUBJECT_MAX_LENGTH,
)
from tildes.typing import AclType


class MessageConversation(DatabaseModel):
    """Model for a message conversation (and the initial message).

    Trigger behavior:
      Incoming:
        - num_replies, last_reply_time, and unread_user_ids are updated when a new
          message_replies row is inserted for the conversation.
        - num_replies and last_reply_time will be updated if a message_replies row is
          deleted.
      Outgoing:
        - Inserting or updating unread_user_ids will update num_unread_messages for all
          relevant users.
    """

    schema_class = MessageConversationSchema

    __tablename__ = "message_conversations"

    conversation_id: int = Column(BigInteger, primary_key=True)
    sender_id: int = Column(
        BigInteger, ForeignKey("users.user_id"), nullable=False, index=True
    )
    recipient_id: int = Column(
        BigInteger, ForeignKey("users.user_id"), nullable=False, index=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )
    subject: str = Column(
        Text,
        CheckConstraint(
            f"LENGTH(subject) <= {SUBJECT_MAX_LENGTH}", name="subject_length"
        ),
        nullable=False,
    )
    markdown: str = deferred(Column(Text, nullable=False))
    rendered_html: str = Column(Text, nullable=False)
    num_replies: int = Column(BigInteger, nullable=False, server_default="0")
    last_reply_time: Optional[datetime] = Column(TIMESTAMP(timezone=True), index=True)

    # This deliberately uses Integer instead of BigInteger, even though that's not
    # correct, because the PostgreSQL intarray extension only supports integers. This
    # is dangerous and *will* break if user_id values ever get larger than integers
    # can hold. I'm comfortable doing something that will only be an issue if the site
    # reaches 2.1 billion users though, I think this would be the least of the problems.
    unread_user_ids: list[int] = Column(
        ARRAY(Integer), nullable=False, server_default="{}"
    )

    sender: User = relationship(
        "User", lazy=False, innerjoin=True, foreign_keys=[sender_id]
    )
    recipient: User = relationship(
        "User", lazy=False, innerjoin=True, foreign_keys=[recipient_id]
    )
    replies: Sequence["MessageReply"] = relationship(
        "MessageReply", order_by="MessageReply.created_time"
    )

    # Create a GIN index on the unread_user_ids column using the gin__int_ops operator
    # class supplied by the intarray module. This should be the best index for "array
    # contains" queries.
    __table_args__ = (
        Index(
            "ix_message_conversations_unread_user_ids_gin",
            unread_user_ids,
            postgresql_using="gin",
            postgresql_ops={"unread_user_ids": "gin__int_ops"},
        ),
    )

    def __init__(self, sender: User, recipient: User, subject: str, markdown: str):
        """Create a new message conversation between two users."""
        self.sender = sender
        self.recipient = recipient
        self.unread_user_ids = [self.recipient.user_id]
        self.subject = subject
        self.markdown = markdown
        self.rendered_html = convert_markdown_to_safe_html(markdown)

    def _update_creation_metric(self) -> None:
        incr_counter("messages", type="conversation")

    def __acl__(self) -> AclType:
        """Pyramid security ACL."""
        acl = []

        # grant permissions to both sender and receiver
        for principal in (self.sender_id, self.recipient_id):
            acl.append((Allow, principal, "view"))
            acl.append((Allow, principal, "reply"))

        acl.append(DENY_ALL)

        return acl

    @property
    def conversation_id36(self) -> str:
        """Return the conversation's ID in ID36 format."""
        return id_to_id36(self.conversation_id)

    @property
    def last_activity_time(self) -> datetime:
        """Return the last time a message was sent in this conversation."""
        if self.last_reply_time:
            return self.last_reply_time

        return self.created_time

    def is_participant(self, user: User) -> bool:
        """Return whether the user is a participant in the conversation."""
        return user in (self.sender, self.recipient)

    def other_user(self, viewer: User) -> User:
        """Return the conversation's other user from viewer's perspective.

        That is, if the viewer is the sender, this will be the recipient, and vice
        versa.
        """
        if not self.is_participant(viewer):
            raise ValueError("User is not a participant in this conversation.")

        if viewer == self.sender:
            return self.recipient

        return self.sender

    def is_unread_by_user(self, user: User) -> bool:
        """Return whether the conversation is unread by the specified user."""
        if not self.is_participant(user):
            raise ValueError("User is not a participant in this conversation.")

        return user.user_id in self.unread_user_ids

    def mark_unread_for_user(self, user: User) -> None:
        """Mark the conversation unread for the specified user.

        Uses the postgresql intarray union operator `|`, so there's no need to worry
        about duplicate values, race conditions, etc.
        """
        if not self.is_participant(user):
            raise ValueError("User is not a participant in this conversation.")

        union = MessageConversation.unread_user_ids.op("|")  # type: ignore
        self.unread_user_ids = union(user.user_id)

    def mark_read_for_user(self, user: User) -> None:
        """Mark the conversation read for the specified user.

        Uses the postgresql intarray "remove element from array" operation, so there's
        no need to worry about whether the value is present or not, race conditions,
        etc.
        """
        if not self.is_participant(user):
            raise ValueError("User is not a participant in this conversation.")

        user_id = user.user_id
        self.unread_user_ids = (
            MessageConversation.unread_user_ids - user_id  # type: ignore
        )


class MessageReply(DatabaseModel):
    """Model for the replies sent to a MessageConversation.

    Trigger behavior:
      Outgoing:
        - Inserting will update num_replies, last_reply_time, and unread_user_ids for
          the relevant conversation.
        - Deleting will update num_replies and last_reply_time for the relevant
          conversation.
    """

    schema_class = MessageReplySchema

    __tablename__ = "message_replies"

    reply_id: int = Column(BigInteger, primary_key=True)
    conversation_id: int = Column(
        BigInteger,
        ForeignKey("message_conversations.conversation_id"),
        nullable=False,
        index=True,
    )
    sender_id: int = Column(
        BigInteger, ForeignKey("users.user_id"), nullable=False, index=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )
    markdown: str = deferred(Column(Text, nullable=False))
    rendered_html: str = Column(Text, nullable=False)

    conversation: MessageConversation = relationship(
        "MessageConversation", innerjoin=True
    )
    sender: User = relationship("User", lazy=False, innerjoin=True)

    def __init__(self, conversation: MessageConversation, sender: User, markdown: str):
        """Add a new reply to a message conversation."""
        self.conversation = conversation
        self.sender = sender
        self.markdown = markdown
        self.rendered_html = convert_markdown_to_safe_html(markdown)

    def _update_creation_metric(self) -> None:
        incr_counter("messages", type="reply")

    @property
    def reply_id36(self) -> str:
        """Return the reply's ID in ID36 format."""
        return id_to_id36(self.reply_id)
