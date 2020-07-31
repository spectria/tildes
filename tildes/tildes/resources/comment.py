# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Root factories for comments."""

from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound
from pyramid.request import Request

from tildes.lib.id import id36_to_id
from tildes.models.comment import Comment, CommentNotification
from tildes.resources import get_resource
from tildes.schemas.comment import CommentSchema
from tildes.views.decorators import use_kwargs


@use_kwargs(CommentSchema(only=("comment_id36",)), location="matchdict")
def comment_by_id36(request: Request, comment_id36: str) -> Comment:
    """Get a comment specified by {comment_id36} in the route (or 404)."""
    query = (
        request.query(Comment)
        .include_removed()
        .filter_by(comment_id=id36_to_id(comment_id36))
    )

    try:
        return get_resource(request, query)
    except HTTPNotFound:
        raise HTTPNotFound("Comment not found (or it was deleted)")


@use_kwargs(CommentSchema(only=("comment_id36",)), location="matchdict")
def notification_by_comment_id36(
    request: Request, comment_id36: str
) -> CommentNotification:
    """Get a comment notification specified by {comment_id36} in the route.

    Looks up a comment notification for the logged-in user with the {comment_id36}
    specified in the route.
    """
    if not request.user:
        raise HTTPForbidden

    comment_id = id36_to_id(comment_id36)
    query = request.query(CommentNotification).filter_by(
        user=request.user, comment_id=comment_id
    )

    return get_resource(request, query)
