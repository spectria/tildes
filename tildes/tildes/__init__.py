# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Configure and initialize the Pyramid app."""

from time import time
from typing import Any, Callable, Dict, Optional, Tuple

from marshmallow.exceptions import ValidationError
from paste.deploy.config import PrefixMiddleware
from prometheus_client import Histogram
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPTooManyRequests
from pyramid.registry import Registry
from pyramid.request import Request
from pyramid.response import Response
from redis import Redis
import sentry_sdk
from sentry_sdk.integrations.pyramid import PyramidIntegration
from webassets import Bundle

from tildes.lib.ratelimit import RATE_LIMITED_ACTIONS, RateLimitResult


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
    config.include("tildes.routes")

    config.add_webasset("javascript", Bundle(output="js/tildes.js"))
    config.add_webasset("javascript-third-party", Bundle(output="js/third_party.js"))
    config.add_webasset("css", Bundle(output="css/tildes.css"))

    config.scan("tildes.views")

    config.add_tween("tildes.http_method_tween_factory")
    config.add_tween("tildes.metrics_tween_factory")
    config.add_tween("tildes.theme_cookie_tween_factory")

    config.add_static_view("images", "/images")

    config.add_request_method(is_safe_request_method, "is_safe_method", reify=True)

    # Add the request.redis request method to access a redis connection. This is done in
    # a bit of a strange way to support being overridden in tests.
    config.registry["redis_connection_factory"] = get_redis_connection
    # pylint: disable=unnecessary-lambda
    config.add_request_method(
        lambda request: config.registry["redis_connection_factory"](request),
        "redis",
        reify=True,
    )
    # pylint: enable=unnecessary-lambda

    config.add_request_method(check_rate_limit, "check_rate_limit")
    config.add_request_method(apply_rate_limit, "apply_rate_limit")

    config.add_request_method(current_listing_base_url, "current_listing_base_url")
    config.add_request_method(current_listing_normal_url, "current_listing_normal_url")

    if settings.get("sentry_dsn"):
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


def http_method_tween_factory(handler: Callable, registry: Registry) -> Callable:
    # pylint: disable=unused-argument
    """Return a tween function that can override the request's HTTP method."""

    def method_override_tween(request: Request) -> Request:
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


def get_redis_connection(request: Request) -> Redis:
    """Return a connection to the Redis server."""
    socket = request.registry.settings["redis.unix_socket_path"]
    return Redis(unix_socket_path=socket)


def is_safe_request_method(request: Request) -> bool:
    """Return whether the request method is "safe" (is GET or HEAD)."""
    return request.method in {"GET", "HEAD"}


def check_rate_limit(request: Request, action_name: str) -> RateLimitResult:
    """Check the rate limit for a particular action on a request."""
    try:
        action = RATE_LIMITED_ACTIONS[action_name]
    except KeyError:
        raise ValueError("Invalid action name: %s" % action_name)

    action.redis = request.redis

    results = []

    if action.by_user and request.user:
        results.append(action.check_for_user_id(request.user.user_id))

    if action.by_ip and request.remote_addr:
        results.append(action.check_for_ip(request.remote_addr))

    # no checks were done, return the "not limited" result
    if not results:
        return RateLimitResult.unlimited_result()

    return RateLimitResult.merged_result(results)


def apply_rate_limit(request: Request, action_name: str) -> None:
    """Check the rate limit for an action, and raise HTTP 429 if it's exceeded."""
    result = request.check_rate_limit(action_name)
    if not result.is_allowed:
        raise result.add_headers_to_response(HTTPTooManyRequests())


def current_listing_base_url(
    request: Request, query: Optional[Dict[str, Any]] = None
) -> str:
    """Return the "base" url for the current listing route.

    The "base" url represents the current listing, including any filtering options (or
    the fact that filters are disabled).

    The `query` argument allows adding query variables to the generated url.
    """
    base_vars_by_route: Dict[str, Tuple[str, ...]] = {
        "bookmarks": ("per_page", "type"),
        "group": ("order", "period", "per_page", "tag", "unfiltered"),
        "home": ("order", "period", "per_page", "tag", "unfiltered"),
        "search": ("order", "period", "per_page", "q"),
        "user": ("per_page", "type"),
    }

    try:
        base_view_vars = base_vars_by_route[request.matched_route.name]
    except KeyError:
        raise AttributeError("Current route is not supported.")

    query_vars = {
        key: val for key, val in request.GET.copy().items() if key in base_view_vars
    }
    if query:
        query_vars.update(query)

    return request.current_route_url(_query=query_vars)


def current_listing_normal_url(
    request: Request, query: Optional[Dict[str, Any]] = None
) -> str:
    """Return the "normal" url for the current listing route.

    The "normal" url represents the current listing without any additional
    filtering-related changes (the user's standard view of that listing).

    The `query` argument allows adding query variables to the generated url.
    """
    normal_vars_by_route: Dict[str, Tuple[str, ...]] = {
        "bookmarks": ("order", "period", "per_page"),
        "group": ("order", "period", "per_page"),
        "home": ("order", "period", "per_page"),
        "notifications": ("per_page",),
        "search": ("order", "period", "per_page", "q"),
        "user": ("per_page",),
    }

    try:
        normal_view_vars = normal_vars_by_route[request.matched_route.name]
    except KeyError:
        raise AttributeError("Current route is not supported.")

    query_vars = {
        key: val for key, val in request.GET.copy().items() if key in normal_view_vars
    }
    if query:
        query_vars.update(query)

    return request.current_route_url(_query=query_vars)
