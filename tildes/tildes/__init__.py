"""Configure and initialize the Pyramid app."""

from typing import Any, Callable, Dict, Optional

from paste.deploy.config import PrefixMiddleware
from pyramid.config import Configurator
from pyramid.registry import Registry
from pyramid.request import Request
from redis import StrictRedis
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
    config.add_webasset("site-icons-css", Bundle(output="css/site-icons.css"))

    config.scan("tildes.views")

    config.add_tween("tildes.http_method_tween_factory")

    config.add_request_method(is_safe_request_method, "is_safe_method", reify=True)

    # Add the request.redis request method to access a redis connection. This
    # is done in a bit of a strange way to support being overridden in tests.
    config.registry["redis_connection_factory"] = get_redis_connection
    # pylint: disable=unnecessary-lambda
    config.add_request_method(
        lambda request: config.registry["redis_connection_factory"](request),
        "redis",
        reify=True,
    )
    # pylint: enable=unnecessary-lambda

    config.add_request_method(check_rate_limit, "check_rate_limit")

    config.add_request_method(current_listing_base_url, "current_listing_base_url")
    config.add_request_method(current_listing_normal_url, "current_listing_normal_url")

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


def get_redis_connection(request: Request) -> StrictRedis:
    """Return a StrictRedis connection to the Redis server."""
    socket = request.registry.settings["redis.unix_socket_path"]
    return StrictRedis(unix_socket_path=socket)


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


def current_listing_base_url(
    request: Request, query: Optional[Dict[str, Any]] = None
) -> str:
    """Return the "base" url for the current listing route.

    The "base" url represents the current listing, including any filtering
    options (or the fact that filters are disabled).

    The `query` argument allows adding query variables to the generated url.
    """
    if request.matched_route.name not in ("home", "group", "user"):
        raise AttributeError("Current route is not supported.")

    base_view_vars = ("order", "period", "per_page", "tag", "type", "unfiltered")
    query_vars = {
        key: val for key, val in request.GET.copy().items() if key in base_view_vars
    }
    if query:
        query_vars.update(query)

    url = request.current_route_url(_query=query_vars)

    # Pyramid seems to %-encode tilde characters unnecessarily, fix that
    return url.replace("%7E", "~")


def current_listing_normal_url(
    request: Request, query: Optional[Dict[str, Any]] = None
) -> str:
    """Return the "normal" url for the current listing route.

    The "normal" url represents the current listing without any additional
    filtering-related changes (the user's standard view of that listing).

    The `query` argument allows adding query variables to the generated url.
    """
    if request.matched_route.name not in ("home", "group", "user"):
        raise AttributeError("Current route is not supported.")

    normal_view_vars = ("order", "period", "per_page")
    query_vars = {
        key: val for key, val in request.GET.copy().items() if key in normal_view_vars
    }
    if query:
        query_vars.update(query)

    url = request.current_route_url(_query=query_vars)

    # Pyramid seems to %-encode tilde characters unnecessarily, fix that
    return url.replace("%7E", "~")
