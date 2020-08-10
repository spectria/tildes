# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views used by Pyramid when an exception is raised."""

from typing import Sequence
from urllib.parse import quote_plus

from marshmallow import ValidationError
from pyramid.httpexceptions import (
    HTTPError,
    HTTPForbidden,
    HTTPFound,
    HTTPNotFound,
    HTTPUnprocessableEntity,
)
from pyramid.request import Request
from pyramid.security import Authenticated
from pyramid.view import (
    exception_view_config,
    forbidden_view_config,
    notfound_view_config,
)
from sqlalchemy import cast, desc, func, Text

from tildes.models.group import Group


def errors_from_validationerror(validation_error: ValidationError) -> Sequence[str]:
    """Extract errors from a marshmallow ValidationError into a displayable format."""
    normalized_errors = validation_error.normalized_messages()

    # As of webargs 6.0, errors are inside a nested dict, where the first level should
    # always be a single-item dict with the key representing the "location" of the data
    # (e.g. query, form, etc.) - Check if the errors seem to be in that format, and if
    # they are, just remove that level since we don't care about it
    first_value = list(normalized_errors.values())[0]
    if isinstance(first_value, dict):
        errors_by_field = first_value
    else:
        # not a webargs error, so just use the original without any unnesting
        errors_by_field = normalized_errors

    error_strings = []
    for field, errors in errors_by_field.items():
        joined_errors = " ".join(errors)
        if field != "_schema":
            error_strings.append(f"{field}: {joined_errors}")
        else:
            error_strings.append(joined_errors)

    return error_strings


@exception_view_config(
    HTTPNotFound, route_name="group", renderer="error_group_not_found.jinja2"
)
def group_not_found(request: Request) -> dict:
    """Show the user a customized 404 page for group names."""
    request.response.status_int = 404
    supplied_name = request.matchdict.get("path")
    # the 'word_similarity' function here is from the 'pg_trgm' extension
    group_suggestions = (
        request.query(Group)
        .filter(func.word_similarity(cast(Group.path, Text), supplied_name) > 0)
        .order_by(desc(func.word_similarity(cast(Group.path, Text), supplied_name)))
        .limit(3)
        .all()
    )
    return {"group_suggestions": group_suggestions, "supplied_name": supplied_name}


@notfound_view_config(xhr=False, renderer="error_page.jinja2")
@forbidden_view_config(
    xhr=False, effective_principals=Authenticated, renderer="error_page.jinja2"
)
@exception_view_config(context=HTTPError, xhr=False, renderer="error_page.jinja2")
def generic_error_page(request: Request) -> dict:
    """Display a generic error page for all HTTP exceptions.

    Note that for 403 errors, this view will only be used if the user is logged in.
    """
    request.response.status_int = request.exception.status_int

    error = f"Error {request.exception.status_code} ({request.exception.title})"

    if isinstance(request.exception, HTTPForbidden):
        description = "You don't have access to this page"
    if isinstance(request.exception, HTTPUnprocessableEntity) and isinstance(
        request.exception.__context__, ValidationError
    ):
        errors = errors_from_validationerror(request.exception.__context__)
        description = " ".join(errors)
    else:
        description = request.exception.explanation

    return {"error": error, "description": description}


@forbidden_view_config(xhr=False)
def logged_out_forbidden(request: Request) -> HTTPFound:
    """Redirect logged-out users to login page on 403 error."""
    forbidden_path = quote_plus(request.path_qs)
    login_url = request.route_url("login", _query={"from_url": forbidden_path})

    return HTTPFound(location=login_url)
