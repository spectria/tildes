# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains Pyramid "tweens", used to insert additional logic into request-handling."""

from time import time
from typing import Callable

from prometheus_client import Histogram
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
        labelnames=["route", "status_code", "method", "logged_in"],
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
        ).observe(duration)

        return response

    return metrics_tween


def theme_cookie_tween_factory(handler: Callable, registry: Registry) -> Callable:
    # pylint: disable=unused-argument
    """Return a tween function that sets the theme cookie."""

    def theme_cookie_tween(request: Request) -> Response:
        """Set the theme cookie if needed (currently always, see comment below)."""
        response = handler(request)

        # only set the cookie on GET requests
        if request.method.upper() != "GET":
            return response

        current_theme = request.cookies.get("theme", "")
        if not current_theme and request.user:
            current_theme = request.user.theme_default

        # Currently, we want to always set the theme cookie. This is because we
        # recently started setting the domain on this cookie (to be able to apply the
        # user's theme to the Blog/Docs sites), and all older cookies won't have a
        # domain set. This will basically let us convert the old no-domain cookies to
        # new ones. After a decent amount of time (maybe sometime in April 2019), we
        # can change this to only set the cookie when it's not already present and the
        # user has a default theme set (so their default theme will work for Blog/Docs).
        if current_theme:
            response.set_cookie(
                "theme",
                current_theme,
                max_age=315360000,
                secure=True,
                domain="." + request.domain,
            )
        return response

    return theme_cookie_tween
