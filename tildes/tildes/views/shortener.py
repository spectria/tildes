# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to the link shortener."""

from mypy_extensions import NoReturn
from pyramid.httpexceptions import HTTPFound, HTTPMovedPermanently
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config


@view_config(route_name="shortener", permission=NO_PERMISSION_REQUIRED)
def get_shortener(request: Request) -> NoReturn:
    """Redirect to the site if someone just visits the base shortener domain."""
    # pylint: disable=unused-argument
    raise HTTPFound(location="https://tildes.net")


@view_config(route_name="shortener_group", permission=NO_PERMISSION_REQUIRED)
def get_shortener_group(request: Request) -> NoReturn:
    """Redirect to the base path of a group."""
    destination = f"https://tildes.net/~{request.context.path}"
    raise HTTPMovedPermanently(location=destination)


@view_config(route_name="shortener_topic", permission=NO_PERMISSION_REQUIRED)
def get_shortener_topic(request: Request) -> NoReturn:
    """Redirect to the full permalink for a topic."""
    destination = f"https://tildes.net{request.context.permalink}"
    raise HTTPMovedPermanently(location=destination)
