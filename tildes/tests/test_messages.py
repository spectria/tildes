# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from pyramid.security import principals_allowed_by_permission
from pytest import fixture, raises

from tildes.models.message import MessageConversation, MessageReply
from tildes.models.user import User
from tildes.schemas.fields import Markdown, SimpleString
from tildes.schemas.message import MessageConversationSchema, MessageReplySchema


@fixture
def conversation(db, session_user, session_user2):
    """Create a message conversation and delete it as teardown."""
    new_conversation = MessageConversation(
        session_user, session_user2, "Subject", "Message"
    )
    db.add(new_conversation)
    db.commit()

    yield new_conversation

    # delete any replies that were added to the conversation
    for reply in new_conversation.replies:
        db.delete(reply)

    db.delete(new_conversation)
    db.commit()


def test_message_conversation_validation(mocker, session_user, session_user2):
    """Ensure a new message conversation goes through expected validation."""
    mocker.spy(MessageConversationSchema, "load")
    mocker.spy(SimpleString, "_validate")
    mocker.spy(Markdown, "_validate")

    MessageConversation(session_user, session_user2, "Subject", "Message")

    assert MessageConversationSchema.load.called
    assert SimpleString._validate.call_args[0][1] == "Subject"
    assert Markdown._validate.call_args[0][1] == "Message"


def test_message_reply_validation(mocker, conversation, session_user2):
    """Ensure a new message reply goes through expected validation."""
    mocker.spy(MessageReplySchema, "load")
    mocker.spy(Markdown, "_validate")

    MessageReply(conversation, session_user2, "A new reply")

    assert MessageReplySchema.load.called
    assert Markdown._validate.call_args[0][1] == "A new reply"


def test_conversation_viewing_permission(conversation):
    """Ensure only the two involved users can view a message conversation."""
    principals = principals_allowed_by_permission(conversation, "view")
    users = {conversation.sender.user_id, conversation.recipient.user_id}
    assert principals == users


def test_conversation_other_user(conversation):
    """Ensure that the "other user" method returns the expected user."""
    sender = conversation.sender
    recipient = conversation.recipient

    assert conversation.other_user(sender) == recipient
    assert conversation.other_user(recipient) == sender


def test_conversation_other_user_invalid(conversation):
    """Ensure that "other user" method fails if the user isn't involved."""
    new_user = User("SomeOutsider", "super amazing password")

    with raises(ValueError):
        assert conversation.other_user(new_user)


def test_replies_affect_num_replies(conversation, db):
    """Ensure adding replies to a conversation affects the reply count."""
    assert conversation.num_replies == 0

    # add replies and ensure each one increases the count
    for num in range(5):
        new_reply = MessageReply(conversation, conversation.recipient, "hi")
        db.add(new_reply)
        db.commit()
        db.refresh(conversation)
        assert conversation.num_replies == num + 1


def test_replies_update_activity_time(conversation, db):
    """Ensure adding replies updates the last activity timestamp."""
    assert conversation.last_activity_time == conversation.created_time

    for _ in range(5):
        new_reply = MessageReply(conversation, conversation.recipient, "hi")
        db.add(new_reply)
        db.commit()

        assert conversation.last_activity_time == new_reply.created_time
