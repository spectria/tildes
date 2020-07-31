# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains decorators for view functions."""

from typing import Any, Callable, Dict, Union

from marshmallow import EXCLUDE
from marshmallow.fields import Field
from marshmallow.schema import Schema
from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.view import view_config
from webargs import dict2schema, pyramidparser


def use_kwargs(
    argmap: Union[Schema, Dict[str, Field]], location: str = "query", **kwargs: Any
) -> Callable:
    """Wrap the webargs @use_kwargs decorator with preferred default modifications.

    Primarily, we want the location argument to default to "query" so that the data
    comes from the query string. As of version 6.0, webargs defaults to "json", which is
    almost never correct for Tildes.

    We also need to set every schema's behavior for unknown fields to "exclude", so that
    it just ignores them, instead of erroring when there's unexpected data (as there
    almost always is, especially because of Intercooler).
    """
    # convert a dict argmap to a Schema (the same way webargs would on its own)
    if isinstance(argmap, dict):
        argmap = dict2schema(argmap)()

    assert isinstance(argmap, Schema)  # tell mypy the type is more restricted now

    argmap.unknown = EXCLUDE

    return pyramidparser.use_kwargs(argmap, location=location, **kwargs)


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
