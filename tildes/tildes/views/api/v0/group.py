# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API v0 endpoints related to groups."""

from pyramid.request import Request

from tildes.api import APIv0
from tildes.resources.group import group_by_path


ONE = APIv0(name="group", path="/groups/{group_path}", factory=group_by_path)


@ONE.get()
def get_group(request: Request) -> dict:
    """Get a single group's data."""
    return request.context
