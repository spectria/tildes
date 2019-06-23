# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains classes related to handling AMQP (rabbitmq) messages."""

import json
import os
from abc import abstractmethod
from typing import Sequence

from amqpy import AbstractConsumer, Connection, Message

from tildes.lib.database import get_session_from_config


class PgsqlQueueConsumer(AbstractConsumer):
    """Base class for consumers of events sent from PostgreSQL via rabbitmq.

    This class is intended to be used in a completely "stand-alone" manner, such as
    inside a script being run separately as a background job. As such, it also includes
    connecting to rabbitmq, declaring the underlying queue and bindings, and
    (optionally) connecting to the database to be able to fetch and modify data as
    necessary. It relies on the environment variable INI_FILE being set.

    Note that all messages received by these consumers are expected to be in JSON
    format.
    """

    PGSQL_EXCHANGE_NAME = "pgsql_events"

    def __init__(
        self, queue_name: str, routing_keys: Sequence[str], uses_db: bool = True
    ):
        """Initialize a new queue, bindings, and consumer for it."""
        self.connection = Connection()
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue_name, durable=True, auto_delete=False)

        for routing_key in routing_keys:
            self.channel.queue_bind(
                queue_name, exchange=self.PGSQL_EXCHANGE_NAME, routing_key=routing_key
            )

        if uses_db:
            self.db_session = get_session_from_config(os.environ["INI_FILE"])
        else:
            self.db_session = None

        super().__init__(self.channel, queue_name)

    def consume_queue(self) -> None:
        """Declare the consumer and consume messages indefinitely."""
        self.declare()
        self.connection.loop()

    @abstractmethod
    def run(self, msg: Message) -> None:
        """Process a delivered message (subclasses must implement)."""
        pass

    def start(self, msg: Message) -> None:
        """Setup/teardown for message-processing (wraps run())."""
        # decode the msg body from JSON
        msg.body = json.loads(msg.body)

        # process the message, will call run()
        super().start(msg)

        # after processing is finished, commit the transaction and ack the msg
        if self.db_session:
            self.db_session.commit()

        msg.ack()
