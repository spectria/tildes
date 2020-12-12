# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define and attach request methods to the Pyramid request object."""

from typing import Any, Dict, Optional, Tuple

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPTooManyRequests
from pyramid.request import Request
from redis import Redis

from tildes.lib.ratelimit import (
    RATE_LIMITED_ACTIONS,
    RateLimitedAction,
    RateLimitResult,
)
from tildes.models.user import UserRateLimit


def get_redis_connection(request: Request) -> Redis:
    """Return a connection to the Redis server."""
    socket = request.registry.settings["redis.unix_socket_path"]
    return Redis(unix_socket_path=socket)


def is_bot(request: Request) -> bool:
    """Return whether the request is by a known bot (e.g. search engine crawlers)."""
    bot_user_agent_substrings = (
        "Amazonbot",
        "bingbot",
        "Googlebot",
        "heritrix",
        "http.rb",
        "qotnews scraper",
        "Prometheus",
        "Python-urllib",
        "Qwantify",
        "SeznamBot",
        "tildee.py",
        "Tildes Scraper",
        "yacybot",
        "YandexBot",
    )

    if request.user_agent:
        return any(
            [substring in request.user_agent for substring in bot_user_agent_substrings]
        )

    return False


def is_safe_request_method(request: Request) -> bool:
    """Return whether the request method is "safe" (is GET or HEAD)."""
    return request.method in {"GET", "HEAD"}


def check_rate_limit(request: Request, action_name: str) -> RateLimitResult:
    """Check the rate limit for a particular action on a request."""
    action = None

    # check for a custom rate-limit for the user
    if request.user:
        user_limit = (
            request.query(UserRateLimit)
            .filter(
                UserRateLimit.user == request.user, UserRateLimit.action == action_name
            )
            .one_or_none()
        )

        if user_limit:
            action = RateLimitedAction(
                action_name,
                user_limit.period,
                user_limit.limit,
                by_user=True,
                by_ip=False,
            )

    # if a custom rate-limit wasn't found, use the default, global rate-limit
    if not action:
        try:
            action = RATE_LIMITED_ACTIONS[action_name]
        except KeyError:
            raise ValueError("Invalid action name: %s" % action_name)

    action.redis = request.redis

    results = []

    if action.is_global:
        results.append(action.check_global())

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
        "group_search": ("order", "period", "per_page", "q"),
        "home": ("order", "period", "per_page", "tag", "unfiltered"),
        "ignored_topics": ("per_page",),
        "search": ("order", "period", "per_page", "q"),
        "user": ("order", "per_page", "type"),
        "user_search": ("order", "per_page", "type", "q"),
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
        "votes": ("order", "period", "per_page"),
        "group": ("order", "period", "per_page"),
        "group_search": ("order", "period", "per_page", "q"),
        "home": ("order", "period", "per_page"),
        "ignored_topics": ("order", "period", "per_page"),
        "notifications": ("per_page",),
        "search": ("order", "period", "per_page", "q"),
        "user": ("order", "per_page"),
        "user_search": ("order", "per_page", "q"),
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


def current_theme(request: Request) -> str:
    """Return the name of the current theme being used by the user."""
    cookie_theme = request.cookies.get("theme", None)

    if request.user:
        user_theme = request.user.theme_default
    else:
        user_theme = None

    return cookie_theme or user_theme or "white"


def includeme(config: Configurator) -> None:
    """Attach the request methods to the Pyramid request object."""
    config.add_request_method(is_bot, "is_bot", reify=True)
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

    config.add_request_method(current_theme, "current_theme", reify=True)

    config.add_request_method(check_rate_limit, "check_rate_limit")
    config.add_request_method(apply_rate_limit, "apply_rate_limit")

    config.add_request_method(current_listing_base_url, "current_listing_base_url")
    config.add_request_method(current_listing_normal_url, "current_listing_normal_url")
