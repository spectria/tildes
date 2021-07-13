# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Configure and initialize the Pyramid app."""

from typing import Dict

import sentry_sdk
from marshmallow.exceptions import ValidationError
from paste.deploy.config import PrefixMiddleware
from pyramid.config import Configurator
from sentry_sdk.integrations.pyramid import PyramidIntegration
from webassets import Bundle


def main(global_config: Dict[str, str], **settings: str) -> PrefixMiddleware:
    """Configure and return a Pyramid WSGI application."""
    config = Configurator(settings=settings)

    config.include("cornice")
    config.include("pyramid_session_redis")
    config.include("pyramid_webassets")

    # include database first so the session and querying are available
    config.include("tildes.database")
    config.include("tildes.auth")
    config.include("tildes.jinja")
    config.include("tildes.json")
    config.include("tildes.request_methods")
    config.include("tildes.routes")
    config.include("tildes.settings")
    config.include("tildes.tweens")

    config.add_webasset("javascript", Bundle(output="js/tildes.js"))
    config.add_webasset("javascript-third-party", Bundle(output="js/third_party.js"))
    config.add_webasset("css", Bundle(output="css/tildes.css"))
    config.add_webasset("site-icons-css", Bundle(output="css/site-icons.css"))

    config.scan("tildes.views")

    config.add_static_view("images", "/images")

    if settings.get("sentry_dsn"):
        # pylint: disable=abstract-class-instantiated
        sentry_sdk.init(
            dsn=settings["sentry_dsn"],
            integrations=[PyramidIntegration()],
            ignore_errors=[ValidationError],
        )

    app = config.make_wsgi_app()

    force_port = global_config.get("prefixmiddleware_force_port")
    if force_port:
        prefixed_app = PrefixMiddleware(app, force_port=force_port)
    else:
        prefixed_app = PrefixMiddleware(app)

    return prefixed_app
