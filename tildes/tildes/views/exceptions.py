# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views used by Pyramid when an exception is raised."""

from pyramid.httpexceptions import HTTPException, HTTPForbidden, HTTPNotFound
from pyramid.request import Request
from pyramid.view import (
    exception_view_config,
    forbidden_view_config,
    notfound_view_config,
)
from sqlalchemy import cast, desc, func, Text

from tildes.models.group import Group


@exception_view_config(
    HTTPNotFound, route_name="group", renderer="error_group_not_found.jinja2"
)
def group_not_found(request: Request) -> dict:
    """Show the user a customized 404 page for group names."""
    request.response.status_int = 404
    supplied_name = request.matchdict.get("group_path")
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
@forbidden_view_config(xhr=False, renderer="error_page.jinja2")
@exception_view_config(context=HTTPException, xhr=False, renderer="error_page.jinja2")
def generic_error_page(request: Request) -> dict:
    """Display a generic error page for all HTTP exceptions."""
    request.response.status_int = request.exception.status_int

    error = f"Error {request.exception.status_code} ({request.exception.title})"

    if isinstance(request.exception, HTTPForbidden):
        description = "You don't have access to this page"
    else:
        description = request.exception.explanation

    return {"error": error, "description": description}
