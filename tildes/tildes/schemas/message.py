# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Validation/dumping schemas for messages."""

from marshmallow import Schema
from marshmallow.fields import DateTime, String

from tildes.schemas.fields import ID36, Markdown, SimpleString


SUBJECT_MAX_LENGTH = 200


class MessageConversationSchema(Schema):
    """Marshmallow schema for message conversations."""

    conversation_id36 = ID36()
    subject = SimpleString(max_length=SUBJECT_MAX_LENGTH)
    markdown = Markdown()
    rendered_html = String(dump_only=True)
    created_time = DateTime(dump_only=True)

    class Meta:
        """Always use strict checking so error handlers are invoked."""

        strict = True


class MessageReplySchema(Schema):
    """Marshmallow schema for message replies."""

    reply_id36 = ID36()
    markdown = Markdown()
    rendered_html = String(dump_only=True)
    created_time = DateTime(dump_only=True)

    class Meta:
        """Always use strict checking so error handlers are invoked."""

        strict = True
