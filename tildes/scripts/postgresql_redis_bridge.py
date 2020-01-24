# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Script that converts NOTIFY events on a PostgreSQL channel to Redis stream entries.

Should be kept running at all times as a service.
"""

import json
import os
from configparser import ConfigParser
from select import select

from redis import Redis
from sqlalchemy.engine.url import make_url
import psycopg2

from tildes.lib.event_stream import REDIS_KEY_PREFIX


NOTIFY_CHANNEL = "postgresql_events"

# Stream entries seem to generally require about 20-50 bytes each, depending on which
# data fields they include. A max length of a million should mean that any individual
# stream shouldn't be able to take up more memory than 50 MB or so.
STREAM_MAX_LENGTH = 1_000_000


def postgresql_redis_bridge(config_path: str) -> None:
    """Listen for NOTIFY events and add them to Redis streams."""
    config = ConfigParser()
    config.read(config_path)

    redis = Redis(unix_socket_path=config.get("app:main", "redis.unix_socket_path"))

    postgresql_url = make_url(config.get("app:main", "sqlalchemy.url"))
    postgresql = psycopg2.connect(
        user=postgresql_url.username, dbname=postgresql_url.database
    )
    postgresql.autocommit = True

    with postgresql.cursor() as cursor:
        cursor.execute(f"listen {NOTIFY_CHANNEL}")

    while True:
        # block until a NOTIFY comes through on the channel
        select([postgresql], [], [])

        # fetch any notifications without needing to execute a query
        postgresql.poll()

        # add each NOTIFY to the specified stream(s), using a Redis pipeline to avoid
        # round trips when there are multiple sent by the same PostgreSQL transaction
        with redis.pipeline(transaction=False) as pipe:
            while postgresql.notifies:
                notify = postgresql.notifies.pop(0)

                # the payload format should be "<destination stream name>:<json dict>"
                try:
                    stream_name, fields_json = notify.payload.split(":", maxsplit=1)
                except ValueError:
                    continue

                try:
                    fields = json.loads(fields_json)
                except json.decoder.JSONDecodeError:
                    continue

                pipe.xadd(
                    f"{REDIS_KEY_PREFIX}{stream_name}",
                    fields,
                    maxlen=STREAM_MAX_LENGTH,
                    approximate=True,
                )

            pipe.execute()


if __name__ == "__main__":
    postgresql_redis_bridge(os.environ["INI_FILE"])
