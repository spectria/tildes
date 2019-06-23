# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Consumer that generates content_metadata for topics."""

from typing import Any, Dict, Sequence

import publicsuffix
from amqpy import Message
from sqlalchemy import cast, func
from sqlalchemy.dialects.postgresql import JSONB

from tildes.lib.amqp import PgsqlQueueConsumer
from tildes.lib.string import extract_text_from_html, truncate_string, word_count
from tildes.lib.url import get_domain_from_url
from tildes.models.topic import Topic


class TopicMetadataGenerator(PgsqlQueueConsumer):
    """Consumer that generates content_metadata for topics."""

    def __init__(self, queue_name: str, routing_keys: Sequence[str]):
        """Initialize the consumer, including the public suffix list."""
        super().__init__(queue_name, routing_keys)

        # download the public suffix list (would be good to add caching here)
        psl_file = publicsuffix.fetch()
        self.public_suffix_list = publicsuffix.PublicSuffixList(psl_file)

    def run(self, msg: Message) -> None:
        """Process a delivered message."""
        topic = (
            self.db_session.query(Topic).filter_by(topic_id=msg.body["topic_id"]).one()
        )

        if topic.is_deleted:
            return

        if topic.is_text_type:
            new_metadata = self._generate_text_metadata(topic)
        elif topic.is_link_type:
            new_metadata = self._generate_link_metadata(topic)

        # update the topic's content_metadata in a way that won't wipe out any existing
        # values, and can handle the column being null
        (
            self.db_session.query(Topic)
            .filter(Topic.topic_id == topic.topic_id)
            .update(
                {
                    "content_metadata": func.coalesce(
                        Topic.content_metadata, cast({}, JSONB)
                    ).op("||")(new_metadata)
                },
                synchronize_session=False,
            )
        )

    @staticmethod
    def _generate_text_metadata(topic: Topic) -> Dict[str, Any]:
        """Generate metadata for a text topic (word count and excerpt)."""
        extracted_text = extract_text_from_html(topic.rendered_html)

        # create a short excerpt by truncating the extracted string
        excerpt = truncate_string(extracted_text, length=200, truncate_at_chars=" ")

        return {"word_count": word_count(extracted_text), "excerpt": excerpt}

    def _generate_link_metadata(self, topic: Topic) -> Dict[str, Any]:
        """Generate metadata for a link topic (domain)."""
        parsed_domain = get_domain_from_url(topic.link)
        domain = self.public_suffix_list.get_public_suffix(parsed_domain)

        return {"domain": domain}


if __name__ == "__main__":
    TopicMetadataGenerator(
        queue_name="topic_metadata_generator.q",
        routing_keys=["topic.created", "topic.edited", "topic.link_edited"],
    ).consume_queue()
