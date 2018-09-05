# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API v0 endpoints related to topics."""

from pyramid.request import Request

from tildes.api import APIv0
from tildes.resources.topic import topic_by_id36


ONE = APIv0(
    name="topic", path="/groups/{group_path}/topics/{topic_id36}", factory=topic_by_id36
)


@ONE.get()
def get_topic(request: Request) -> dict:
    """Get a single topic's data."""
    return request.context
