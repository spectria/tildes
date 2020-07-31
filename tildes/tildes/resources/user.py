# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Root factories for users."""

from pyramid.request import Request

from tildes.models.user import User
from tildes.resources import get_resource
from tildes.schemas.user import UserSchema
from tildes.views.decorators import use_kwargs


@use_kwargs(UserSchema(only=("username",)), location="matchdict")
def user_by_username(request: Request, username: str) -> User:
    """Get a user specified by {username} in the route or 404 if not found."""
    query = request.query(User).include_deleted().filter(User.username == username)

    return get_resource(request, query)
