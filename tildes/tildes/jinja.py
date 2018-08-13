"""Contains configuration, functions, etc. for the Jinja template system."""

from typing import Any

from pyramid.config import Configurator

from tildes.lib.datetime import descriptive_timedelta
from tildes.models.comment import Comment
from tildes.models.group import Group
from tildes.models.topic import Topic


def is_comment(item: Any) -> bool:
    """Return whether the item is a Comment."""
    return isinstance(item, Comment)


def is_group(item: Any) -> bool:
    """Return whether the item is a Group."""
    return isinstance(item, Group)


def is_topic(item: Any) -> bool:
    """Return whether the item is a Topic."""
    return isinstance(item, Topic)


def includeme(config: Configurator) -> None:
    """Configure Jinja2 template renderer."""
    settings = config.get_settings()

    settings["jinja2.lstrip_blocks"] = True
    settings["jinja2.trim_blocks"] = True
    settings["jinja2.undefined"] = "strict"

    # add custom jinja filters
    settings["jinja2.filters"] = {"ago": descriptive_timedelta}

    # add custom jinja tests
    settings["jinja2.tests"] = {
        "comment": is_comment,
        "group": is_group,
        "topic": is_topic,
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
