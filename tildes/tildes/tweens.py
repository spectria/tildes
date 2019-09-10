# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains Pyramid "tweens", used to insert additional logic into request-handling."""

from time import time
from typing import Callable

from prometheus_client import Histogram
from pyramid.registry import Registry
from pyramid.request import Request
from pyramid.response import Response

from tildes.metrics import incr_counter


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
        """Set the theme cookie if needed.

        Will only set a cookie if the user has a default theme set for their account
        but doesn't already have a theme cookie. This is necessary so that their default
        theme will apply to the Blog and Docs sites as well, since those sites are
        static and can't look up the user's default theme in the database.

        Temporarily, this tween is also being used to convert old theme cookies with
        "light" or "dark" values to the new "solarized-light" and "solarized-dark" ones.
        """
        response = handler(request)

        # only set the cookie on GET requests
        if request.method.upper() != "GET":
            return response

        current_theme = request.cookies.get("theme", "")

        # if they already have a valid theme cookie, we don't need to do anything
        if current_theme and current_theme not in ("light", "dark"):
            return response

        if current_theme in ("light", "dark"):
            # add the "solarized-" prefix to "light" / "dark" values
            new_theme = "solarized-" + current_theme
        elif request.user and request.user.theme_default:
            # otherwise (no theme cookie), set as the user's default
            new_theme = request.user.theme_default
        else:
            # if the user isn't logged in or doesn't have a default, do nothing
            return response

        response.set_cookie(
            "theme",
            new_theme,
            max_age=315360000,
            secure=True,
            domain="." + request.domain,
        )
        incr_counter("theme_cookie_tween_sets")

        return response

    return theme_cookie_tween
