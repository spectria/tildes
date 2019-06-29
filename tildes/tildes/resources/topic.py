# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Root factories for topics."""

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.request import Request
from webargs.pyramidparser import use_kwargs

from tildes.lib.id import id36_to_id
from tildes.models.topic import Topic
from tildes.resources import get_resource
from tildes.schemas.topic import TopicSchema


@use_kwargs(TopicSchema(only=("topic_id36",)), locations=("matchdict",))
def topic_by_id36(request: Request, topic_id36: str) -> Topic:
    """Get a topic specified by {topic_id36} in the route (or 404)."""
    try:
        topic_id = id36_to_id(topic_id36)
    except ValueError:
        raise HTTPNotFound

    query = (
        request.query(Topic)
        .include_deleted()
        .include_removed()
        .filter_by(topic_id=topic_id)
    )

    try:
        topic = get_resource(request, query)
    except HTTPNotFound:
        raise HTTPNotFound("Topic not found (or it was deleted)")

    # if there's also a group specified in the route, check that it's the same group as
    # the topic was posted in, otherwise redirect to correct group
    if "group_path" in request.matchdict:
        path_from_route = request.matchdict["group_path"].lower()
        if path_from_route != topic.group.path:
            raise HTTPFound(topic.permalink)

    return topic
