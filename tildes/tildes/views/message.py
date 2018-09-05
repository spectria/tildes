# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to sending and viewing messages."""

from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.sql.expression import and_, or_
from webargs.pyramidparser import use_kwargs

from tildes.models.message import MessageConversation, MessageReply
from tildes.schemas.message import MessageConversationSchema, MessageReplySchema


@view_config(
    route_name="new_message", renderer="new_message.jinja2", permission="message"
)
def get_new_message_form(request: Request) -> dict:
    """Form for entering a new private message to send."""
    return {"user": request.context}


@view_config(route_name="messages", renderer="messages.jinja2")
def get_user_messages(request: Request) -> dict:
    """Show the logged-in user's message conversations."""
    # select conversations where either the user is the recipient, or they were the
    # sender and there is at least one reply (don't need to show conversations the user
    # started but haven't been replied to)
    conversations = (
        request.query(MessageConversation)
        .filter(
            or_(
                MessageConversation.recipient == request.user,
                and_(
                    MessageConversation.sender == request.user,
                    MessageConversation.num_replies > 0,
                ),
            )
        )
        .all()
    )

    conversations.sort(key=lambda c: c.last_activity_time, reverse=True)

    return {"conversations": conversations}


@view_config(route_name="messages_unread", renderer="messages_unread.jinja2")
def get_user_unread_messages(request: Request) -> dict:
    """Show the logged-in user's unread message conversations."""
    conversations = (
        request.query(MessageConversation)
        .filter(
            MessageConversation.unread_user_ids.contains(  # type: ignore
                array([request.user.user_id])
            )
        )
        .all()
    )

    conversations.sort(key=lambda c: c.last_activity_time, reverse=True)

    return {"conversations": conversations}


@view_config(route_name="messages_sent", renderer="messages_sent.jinja2")
def get_user_sent_messages(request: Request) -> dict:
    """Show the logged-in user's sent message conversations."""
    # select conversations where either the user was the sender, or they were the
    # recipient and there is at least one reply
    conversations = (
        request.query(MessageConversation)
        .filter(
            or_(
                MessageConversation.sender == request.user,
                and_(
                    MessageConversation.recipient == request.user,
                    MessageConversation.num_replies > 0,
                ),
            )
        )
        .all()
    )

    conversations.sort(key=lambda c: c.last_activity_time, reverse=True)

    return {"conversations": conversations}


@view_config(
    route_name="message_conversation",
    request_method="GET",
    renderer="message_conversation.jinja2",
    permission="view",
)
def get_message_conversation(request: Request) -> dict:
    """View an individual message conversation."""
    conversation = request.context

    conversation.mark_read_for_user(request.user)

    return {"conversation": conversation}


@view_config(
    route_name="message_conversation", request_method="POST", permission="reply"
)
@use_kwargs(MessageReplySchema(only=("markdown",)))
def post_message_reply(request: Request, markdown: str) -> HTTPFound:
    """Post a reply to a message conversation."""
    conversation = request.context
    new_reply = MessageReply(
        conversation=conversation, sender=request.user, markdown=markdown
    )
    request.db_session.add(new_reply)

    conversation_url = request.route_url(
        "message_conversation", conversation_id36=conversation.conversation_id36
    )
    raise HTTPFound(location=conversation_url)


@view_config(route_name="user_messages", request_method="POST", permission="message")
@use_kwargs(MessageConversationSchema(only=("subject", "markdown")))
def post_user_message(request: Request, subject: str, markdown: str) -> HTTPFound:
    """Start a new message conversation with a user."""
    new_conversation = MessageConversation(
        sender=request.user,
        recipient=request.context,
        subject=subject,
        markdown=markdown,
    )
    request.db_session.add(new_conversation)

    user_url = request.route_url("user", username=request.context.username)
    raise HTTPFound(location=user_url)
