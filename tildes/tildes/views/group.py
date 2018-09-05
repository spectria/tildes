# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to groups."""

from pyramid.request import Request
from pyramid.view import view_config

from tildes.models.group import Group


@view_config(route_name="groups", renderer="groups.jinja2")
def get_list_groups(request: Request) -> dict:
    """Show a list of all groups."""
    groups = request.query(Group).order_by(Group.path).all()

    return {"groups": groups}
