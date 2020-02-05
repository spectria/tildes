# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Consumer that generates content_metadata for topics."""

from typing import Any, Dict, Sequence
from ipaddress import ip_address

import publicsuffix
from sqlalchemy import cast, func
from sqlalchemy.dialects.postgresql import JSONB

from tildes.lib.event_stream import EventStreamConsumer, Message
from tildes.lib.string import extract_text_from_html, truncate_string, word_count
from tildes.lib.url import get_domain_from_url
from tildes.models.topic import Topic


class TopicMetadataGenerator(EventStreamConsumer):
    """Consumer that generates content_metadata for topics."""

    def __init__(self, consumer_group: str, source_streams: Sequence[str]):
        """Initialize the consumer, including the public suffix list."""
        super().__init__(consumer_group, source_streams)

        # download the public suffix list (would be good to add caching here)
        psl_file = publicsuffix.fetch()
        self.public_suffix_list = publicsuffix.PublicSuffixList(psl_file)

    def process_message(self, message: Message) -> None:
        """Process a message from the stream."""
        topic = (
            self.db_session.query(Topic)
            .filter_by(topic_id=message.fields["topic_id"])
            .one()
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

    def _domain_is_ip_address(self, domain: str) -> bool:
        """Return whether a "domain" is actually an IP address."""
        try:
            ip_address(domain)
            return True
        except ValueError:
            return False

    def _generate_link_metadata(self, topic: Topic) -> Dict[str, Any]:
        """Generate metadata for a link topic (domain)."""
        parsed_domain = get_domain_from_url(topic.link)

        if self._domain_is_ip_address(parsed_domain):
            domain = parsed_domain
        else:
            domain = self.public_suffix_list.get_public_suffix(parsed_domain)

        return {"domain": domain}


if __name__ == "__main__":
    TopicMetadataGenerator(
        "topic_metadata_generator",
        source_streams=[
            "topics.insert",
            "topics.update.markdown",
            "topics.update.link",
        ],
    ).consume_streams()
