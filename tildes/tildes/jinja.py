# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains configuration, functions, etc. for the Jinja template system."""

from urllib.parse import quote_plus

from pyramid.config import Configurator

from tildes.lib.datetime import (
    adaptive_date,
    descriptive_timedelta,
    vague_timedelta_description,
)
from tildes.models.comment import Comment
from tildes.models.group import Group
from tildes.models.topic import Topic


def includeme(config: Configurator) -> None:
    """Configure Jinja2 template renderer."""
    settings = config.get_settings()

    settings["jinja2.lstrip_blocks"] = True
    settings["jinja2.trim_blocks"] = True

    # add custom jinja filters
    settings["jinja2.filters"] = {
        "adaptive_date": adaptive_date,
        "ago": descriptive_timedelta,
        "quote_plus": quote_plus,
        "vague_timedelta_description": vague_timedelta_description,
    }

    # add custom jinja tests
    settings["jinja2.tests"] = {
        "comment": lambda obj: isinstance(obj, Comment),
        "group": lambda obj: isinstance(obj, Group),
        "topic": lambda obj: isinstance(obj, Topic),
    }

    config.include("pyramid_jinja2")

    config.add_jinja2_search_path("tildes:templates/")

    config.add_jinja2_extension("jinja2.ext.do")
    config.add_jinja2_extension("webassets.ext.jinja2.AssetsExtension")

    # attach webassets to jinja2 environment (via scheduled action)
    def attach_webassets_to_jinja2() -> None:
        jinja2_env = config.get_jinja2_environment()
        jinja2_env.assets_environment = config.get_webassets_env()

    config.action(None, attach_webassets_to_jinja2, order=999)
