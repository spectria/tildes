# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains classes related to handling the Redis-based event streams."""

import os
from abc import abstractmethod
from configparser import ConfigParser
from typing import Any, Dict, List, Sequence

from redis import Redis, ResponseError

from tildes.lib.database import get_session_from_config

REDIS_KEY_PREFIX = "event_stream:"
MAX_RETRIES_PER_MESSAGE = 3


class Message:
    """Represents a single message taken from a stream."""

    def __init__(
        self, redis: Redis, stream: str, message_id: str, fields: Dict[str, str]
    ):
        """Initialize a new message from a Redis stream."""
        self.redis = redis
        self.stream = stream
        self.message_id = message_id
        self.fields = fields

    def ack(self, consumer_group: str) -> None:
        """Acknowledge the message, removing it from the pending entries list."""
        self.redis.xack(
            f"{REDIS_KEY_PREFIX}{self.stream}", consumer_group, self.message_id
        )


class EventStreamConsumer:
    """Base class for consumers of events retrieved from a stream in Redis.

    This class is intended to be used in a completely "stand-alone" manner, such as
    inside a script being run separately as a background job. As such, it also includes
    connecting to Redis, creating the consumer group and the relevant streams, and
    (optionally) connecting to the database to be able to fetch and modify data as
    necessary. It relies on the environment variable INI_FILE being set.
    """

    def __init__(
        self,
        consumer_group: str,
        source_streams: Sequence[str],
        uses_db: bool = True,
        skip_pending: bool = False,
    ):
        """Initialize a new consumer, creating consumer groups and streams if needed."""
        ini_file_path = os.environ["INI_FILE"]
        config = ConfigParser()
        config.read(ini_file_path)

        self.redis = Redis(
            unix_socket_path=config.get("app:main", "redis.unix_socket_path")
        )
        self.consumer_group = consumer_group
        self.source_streams = [
            f"{REDIS_KEY_PREFIX}{stream}" for stream in source_streams
        ]

        # hardcoded for now, will need to change for multiple consumers in same group
        self.name = f"{consumer_group}-1"

        # create all the consumer groups and streams (if necessary)
        for stream in self.source_streams:
            try:
                self.redis.xgroup_create(stream, consumer_group, mkstream=True)
            except ResponseError as error:
                # if the consumer group already exists, a BUSYGROUP error will be
                # returned, so we want to ignore that one but raise anything else
                if not str(error).startswith("BUSYGROUP"):
                    raise

        if uses_db:
            self.db_session = get_session_from_config(ini_file_path)
        else:
            self.db_session = None

        # start by reading any already-pending messages by default
        self.is_reading_pending = not skip_pending

    def consume_streams(self) -> None:
        """Process messages from the streams indefinitely."""
        while True:
            if self.is_reading_pending:
                # clear out any persistently-failing messages first
                self._clear_dead_messages()

                messages = self._get_messages(pending=True)

                # when no pending messages are left, switch to waiting for new ones
                if not messages:
                    self.is_reading_pending = False
            else:
                messages = self._get_messages(pending=False)

            for message in messages:
                self.process_message(message)

                # after processing finishes, commit the transaction and ack the message
                if self.db_session:
                    self.db_session.commit()

                message.ack(self.consumer_group)

    def _clear_dead_messages(self) -> None:
        """Clear any pending messages that have failed too many times.

        If a message seems to be failing consistently, this will use XCLAIM to transfer
        ownership to a fake "consumer" named <consumer group name>-dead. Pending
        messages for -dead consumers should be monitored and inspected manually to
        determine why they were unable to be processed.
        """
        # for each stream, use XPENDING to check for messages that have been delivered
        # repeatedly (indicating that they're failing consistently)
        for stream in self.source_streams:
            response = self.redis.xpending_range(
                stream,
                self.consumer_group,
                min="-",
                max="+",
                count=100,  # there shouldn't ever be more than one, but won't hurt
                consumername=self.name,
            )

            for entry in response:
                # if it hasn't had many attempts yet, leave it pending to try again
                if entry["times_delivered"] < MAX_RETRIES_PER_MESSAGE:
                    continue

                self.redis.xclaim(
                    stream,
                    self.consumer_group,
                    f"{self.consumer_group}-dead",
                    min_idle_time=0,  # shouldn't have to worry about race condition
                    message_ids=[entry["message_id"]],
                )

    def _xreadgroup_response_to_messages(self, response: Any) -> List[Message]:
        """Convert a response from XREADGROUP to a list of Messages."""
        messages = []

        # responses come back in an ugly format, a list of (one for each stream):
        # [b'<stream name>', [(b'<entry id>', {<entry fields, all bytestrings>})]]
        for stream_response in response:
            stream_name = stream_response[0].decode("utf-8")

            for entry in stream_response[1]:
                message = Message(
                    self.redis,
                    stream_name[len(REDIS_KEY_PREFIX) :],
                    message_id=entry[0].decode("utf-8"),
                    fields={
                        key.decode("utf-8"): value.decode("utf-8")
                        for key, value in entry[1].items()
                    },
                )
                messages.append(message)

        return messages

    def _get_messages(self, pending: bool = False) -> List[Message]:
        """Get any messages from the streams for this consumer.

        This method will return at most one message from each of the source streams per
        call.

        If pending is True, the messages will be ones previously delivered to this
        consumer but not acked.

        If pending is False, messages will be ones that haven't been delivered to any
        consumer in this group, and this method will block indefinitely until there are
        messages available.
        """
        if pending:
            message_id = "0"
        else:
            message_id = ">"

        response = self.redis.xreadgroup(
            self.consumer_group,
            self.name,
            {stream: message_id for stream in self.source_streams},
            count=1,
            block=0,
        )

        return self._xreadgroup_response_to_messages(response)

    @abstractmethod
    def process_message(self, message: Message) -> None:
        """Process a message from the stream (subclasses must implement)."""
        pass
