# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains custom JSON serializers for Pyramid's renderer."""

from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.request import Request

from tildes.models import DatabaseModel
from tildes.models.group import Group
from tildes.models.topic import Topic
from tildes.models.user import User


def serialize_model(model_item: DatabaseModel, request: Request) -> dict:
    """Return serializable data for a DatabaseModel item.

    Uses the .schema class attribute to serialize a model by using its corresponding
    marshmallow schema.
    """
    # pylint: disable=unused-argument
    return model_item.schema.dump(model_item)


def serialize_topic(topic: Topic, request: Request) -> dict:
    """Return serializable data for a Topic."""
    context = {}
    if not request.has_permission("view_author", topic):
        context["hide_username"] = True

    return topic.schema_class(context=context).dump(topic)


def includeme(config: Configurator) -> None:
    """Update the JSON renderer with custom serializers."""
    json_renderer = JSON()

    # add generic DatabaseModel adapters
    for model_class in (Group, User):
        json_renderer.add_adapter(model_class, serialize_model)

    # add specific adapters
    json_renderer.add_adapter(Topic, serialize_topic)

    config.add_renderer("json", json_renderer)
