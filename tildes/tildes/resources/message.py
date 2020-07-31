# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Root factories for messages."""

from pyramid.request import Request

from tildes.lib.id import id36_to_id
from tildes.models.message import MessageConversation
from tildes.resources import get_resource
from tildes.schemas.message import MessageConversationSchema
from tildes.views.decorators import use_kwargs


@use_kwargs(
    MessageConversationSchema(only=("conversation_id36",)), location="matchdict"
)
def message_conversation_by_id36(
    request: Request, conversation_id36: str
) -> MessageConversation:
    """Get a conversation specified by {conversation_id36} in the route."""
    query = request.query(MessageConversation).filter_by(
        conversation_id=id36_to_id(conversation_id36)
    )

    return get_resource(request, query)
