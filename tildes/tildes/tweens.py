# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains Pyramid "tweens", used to insert additional logic into request-handling."""

from time import time
from typing import Callable

from prometheus_client import Histogram
from pyramid.config import Configurator
from pyramid.registry import Registry
from pyramid.request import Request
from pyramid.response import Response


def http_method_tween_factory(handler: Callable, registry: Registry) -> Callable:
    # pylint: disable=unused-argument
    """Return a tween function that can override the request's HTTP method."""

    def method_override_tween(request: Request) -> Response:
        """Override HTTP method with one specified in header."""
        valid_overrides_by_method = {"POST": ["DELETE", "PATCH", "PUT"]}

        original_method = request.method.upper()
        valid_overrides = valid_overrides_by_method.get(original_method, [])
        override = request.headers.get("X-HTTP-Method-Override", "").upper()

        if override in valid_overrides:
            request.method = override

        return handler(request)

    return method_override_tween


def metrics_tween_factory(handler: Callable, registry: Registry) -> Callable:
    # pylint: disable=unused-argument
    """Return a tween function that gathers metrics for Prometheus."""

    request_histogram = Histogram(
        "tildes_pyramid_requests_seconds",
        "Request processing times",
        labelnames=["route", "status_code", "method", "logged_in", "is_bot"],
    )

    def metrics_tween(request: Request) -> Response:
        """Gather metrics for each request."""
        start_time = time()
        response = handler(request)
        duration = time() - start_time

        # ignore requests for invalid addresses
        if not request.matched_route:
            return response

        request_histogram.labels(
            route=request.matched_route.name,
            status_code=response.status_code,
            method=request.method,
            logged_in=str(bool(request.user)).lower(),
            is_bot=str(request.is_bot).lower(),
        ).observe(duration)

        return response

    return metrics_tween


def theme_cookie_tween_factory(handler: Callable, registry: Registry) -> Callable:
    # pylint: disable=unused-argument
    """Return a tween function that sets the theme cookie."""

    def theme_cookie_tween(request: Request) -> Response:
        """Set the theme cookie if needed.

        Will only set a cookie if the user has a default theme set for their account
        but doesn't already have a theme cookie. This is necessary so that their default
        theme will apply to the Blog and Docs sites as well, since those sites are
        static and can't look up the user's default theme in the database.
        """
        response = handler(request)

        # only set the cookie on GET requests
        if request.method.upper() != "GET":
            return response

        # if they already have a theme cookie, we don't need to do anything
        if request.cookies.get("theme", ""):
            return response

        # if the user doesn't have a default theme, we don't need to do anything
        if not request.user or not request.user.theme_default:
            return response

        # set a cookie with the user's default theme
        response.set_cookie(
            "theme",
            request.user.theme_default,
            max_age=315360000,
            secure=True,
            domain="." + request.domain,
        )

        return response

    return theme_cookie_tween


def includeme(config: Configurator) -> None:
    """Attach Tildes tweens to the Pyramid config."""
    config.add_tween("tildes.tweens.http_method_tween_factory")
    config.add_tween("tildes.tweens.metrics_tween_factory")
    config.add_tween("tildes.tweens.theme_cookie_tween_factory")
