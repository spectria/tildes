# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains decorators for view functions."""

from typing import Any, Callable

from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.view import view_config


def ic_view_config(**kwargs: Any) -> Callable:
    """Wrap the @view_config decorator for Intercooler views."""
    if "route_name" in kwargs:
        kwargs["route_name"] = "ic_" + kwargs["route_name"]

    if "renderer" in kwargs:
        kwargs["renderer"] = "intercooler/" + kwargs["renderer"]

    if "header" in kwargs:
        raise ValueError("Can't add a header check to Intercooler view.")
    kwargs["header"] = "X-IC-Request:true"

    return view_config(**kwargs)


def rate_limit_view(action_name: str) -> Callable:
    """Decorate a view function to rate-limit calls to it.

    Needs to be used with the name of the rate-limited action, such as:
    @rate_limit_view('register')

    If the ratelimit check comes back with the action being blocked, a 429 response with
    appropriate headers will be raised instead of calling the decorated view.
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = args[0]

            request.apply_rate_limit(action_name)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def not_logged_in(func: Callable) -> Callable:
    """Decorate a view function to prevent access by logged-in users.

    If a logged-in user attempts to access a view decorated by this function, they will
    be redirected to the home page instead. This is useful for views such as the login
    page, registration page, etc. which only logged-out users should be accessing.
    """

    def wrapper(request: Request, **kwargs: Any) -> Any:
        if request.user:
            raise HTTPFound(location=request.route_url("home"))

        return func(request, **kwargs)

    return wrapper
