# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views used by Pyramid when an exception is raised."""

from pyramid.httpexceptions import HTTPNotFound
from pyramid.request import Request
from pyramid.view import forbidden_view_config, exception_view_config
from sqlalchemy import cast, desc, func, Text

from tildes.models.group import Group


@forbidden_view_config(xhr=False, renderer="error_403.jinja2")
def forbidden(request: Request) -> dict:
    """403 Forbidden page."""
    request.response.status_int = 403
    return {}


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
