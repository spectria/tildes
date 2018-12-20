# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to the link shortener."""

from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config


@view_config(route_name="shortener")
def get_shortener(request: Request) -> Response:
    """Display a message if someone just visits the base shortener domain."""
    # pylint: disable=unused-argument
    return Response("Link-shortener for tildes.net")


@view_config(route_name="shortener_group")
def get_shortener_group(request: Request) -> HTTPFound:
    """Redirect to the base path of a group."""
    raise HTTPFound(location=f"/~{request.context.path}")


@view_config(route_name="shortener_topic")
def get_shortener_topic(request: Request) -> HTTPFound:
    """Redirect to the full permalink for a topic."""
    raise HTTPFound(location=request.context.permalink)
