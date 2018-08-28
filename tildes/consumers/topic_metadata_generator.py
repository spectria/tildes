"""Consumer that generates content_metadata for topics."""

from typing import Sequence

from amqpy import Message
import publicsuffix

from tildes.lib.amqp import PgsqlQueueConsumer
from tildes.lib.string import extract_text_from_html, truncate_string, word_count
from tildes.lib.url import get_domain_from_url
from tildes.models.topic import Topic


class TopicMetadataGenerator(PgsqlQueueConsumer):
    """Consumer that generates content_metadata for topics."""

    def __init__(self, queue_name: str, routing_keys: Sequence[str]) -> None:
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

        if topic.is_text_type:
            self._generate_text_metadata(topic)
        elif topic.is_link_type:
            self._generate_link_metadata(topic)

    @staticmethod
    def _generate_text_metadata(topic: Topic) -> None:
        """Generate metadata for a text topic (word count and excerpt)."""
        extracted_text = extract_text_from_html(topic.rendered_html)

        # create a short excerpt by truncating the extracted string
        excerpt = truncate_string(extracted_text, length=200, truncate_at_chars=" ")

        topic.content_metadata = {
            "word_count": word_count(extracted_text),
            "excerpt": excerpt,
        }

    def _generate_link_metadata(self, topic: Topic) -> None:
        """Generate metadata for a link topic (domain)."""
        if not topic.link:
            return

        parsed_domain = get_domain_from_url(topic.link)
        domain = self.public_suffix_list.get_public_suffix(parsed_domain)

        topic.content_metadata = {"domain": domain}


if __name__ == "__main__":
    TopicMetadataGenerator(
        queue_name="topic_metadata_generator.q",
        routing_keys=["topic.created", "topic.edited"],
    ).consume_queue()
