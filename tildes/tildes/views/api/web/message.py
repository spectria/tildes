# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Web API endpoints related to messages."""

from pyramid.request import Request
from webargs.pyramidparser import use_kwargs

from tildes.models.message import MessageReply
from tildes.schemas.message import MessageReplySchema
from tildes.views.decorators import ic_view_config


@ic_view_config(
    route_name="message_conversation_replies",
    request_method="POST",
    renderer="single_message.jinja2",
    permission="reply",
)
@use_kwargs(MessageReplySchema(only=("markdown",)))
def post_message_reply(request: Request, markdown: str) -> dict:
    """Post a reply to a message conversation with Intercooler."""
    conversation = request.context
    new_reply = MessageReply(
        conversation=conversation, sender=request.user, markdown=markdown
    )
    request.db_session.add(new_reply)

    # commit and then re-query the reply to get complete data
    request.tm.commit()

    new_reply = (
        request.query(MessageReply)
        .join_all_relationships()
        .filter_by(reply_id=new_reply.reply_id)
        .one()
    )

    return {"message": new_reply}
