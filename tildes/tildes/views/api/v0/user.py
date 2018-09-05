# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API v0 endpoints related to users."""

from pyramid.request import Request

from tildes.api import APIv0
from tildes.resources.user import user_by_username


ONE = APIv0(name="user", path="/users/{username}", factory=user_by_username)


@ONE.get()
def get_user(request: Request) -> dict:
    """Get a single user's data."""
    return request.context
