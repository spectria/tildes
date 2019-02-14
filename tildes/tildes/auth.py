# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Configuration and functionality related to authentication/authorization."""

from typing import Any, Optional, Sequence

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.security import Allow, Everyone

from tildes.models.user import User


class DefaultRootFactory:
    """Default root factory to grant everyone 'view' permission by default.

    Note that this will only be applied in cases where a view does not have a factory
    specified at all (so request.context doesn't have a meaningful value). Any classes
    that could be returned by a root factory must have an __acl__ defined, they will not
    "fall back" to this one.
    """

    __acl__ = ((Allow, Everyone, "view"),)

    def __init__(self, request: Request):
        """Root factory constructor - must take a request argument."""
        pass


def get_authenticated_user(request: Request) -> Optional[User]:
    """Return the User object for the authed user making the request."""
    user_id = request.unauthenticated_userid
    if not user_id:
        return None

    query = request.query(User).filter_by(user_id=user_id)

    return query.one_or_none()


def auth_callback(user_id: int, request: Request) -> Optional[Sequence[str]]:
    """Return authorization principals for a user_id from the session.

    This is a callback function needed by SessionAuthenticationPolicy. It should return
    None if the user_id does not exist (such as a deleted user).
    """
    if not request.user:
        return None

    # if the user is deleted or banned, log them out
    # (is there a better place to do this?)
    if request.user.is_banned or request.user.is_deleted:
        request.session.invalidate()
        raise HTTPFound("/")

    if user_id != request.user.user_id:
        raise AssertionError("auth_callback called with different user_id")

    return request.user.auth_principals


def includeme(config: Configurator) -> None:
    """Config updates related to authentication/authorization."""
    # make all views require "view" permission unless specifically overridden
    config.set_default_permission("view")

    # replace the default root factory with a custom one to more easily support the
    # default permission
    config.set_root_factory(DefaultRootFactory)

    config.set_authorization_policy(ACLAuthorizationPolicy())

    config.set_authentication_policy(
        SessionAuthenticationPolicy(callback=auth_callback)
    )

    # enable CSRF checking globally by default
    config.set_default_csrf_options(require_csrf=True)

    # make the logged-in User object available as request.user
    config.add_request_method(get_authenticated_user, "user", reify=True)

    # add has_any_permission method for easily checking multiple permissions
    config.add_request_method(has_any_permission, "has_any_permission")


def has_any_permission(
    request: Request, permissions: Sequence[str], context: Any
) -> bool:
    """Return whether the user has any of the permissions on the item."""
    return any(
        request.has_permission(permission, context) for permission in permissions
    )
