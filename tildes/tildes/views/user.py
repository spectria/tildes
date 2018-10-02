# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to a specific user."""

from typing import List, Optional, Union

from marshmallow.fields import String
from marshmallow.validate import OneOf
from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql.expression import desc
from webargs.pyramidparser import use_kwargs

from tildes.enums import CommentLabelOption
from tildes.models.comment import Comment
from tildes.models.topic import Topic
from tildes.models.user import User, UserInviteCode
from tildes.schemas.listing import PaginatedListingSchema


def _get_user_recent_activity(
    request: Request, user: User
) -> List[Union[Comment, Topic]]:
    page_size = 20

    # Since we don't know how many comments or topics will be needed to make up a page,
    # we'll fetch the full page size of both types, merge them, and then trim down to
    # the size afterwards
    query = (
        request.query(Comment)
        .filter(Comment.user == user)
        .order_by(desc(Comment.created_time))
        .limit(page_size)
        .join_all_relationships()
    )

    # include removed comments if the user's looking at their own page or is an admin
    if user == request.user or request.user.is_admin:
        query = query.include_removed()

    comments = query.all()

    query = (
        request.query(Topic)
        .filter(Topic.user == user)
        .order_by(desc(Topic.created_time))
        .limit(page_size)
        .join_all_relationships()
    )

    # include removed topics if the user's looking at their own page or is an admin
    if user == request.user or request.user.is_admin:
        query = query.include_removed()

    topics = query.all()

    merged_posts = sorted(
        comments + topics,  # this order so topic comes first when times match
        key=lambda post: post.created_time,
        reverse=True,
    )
    merged_posts = merged_posts[:page_size]

    return merged_posts


@view_config(route_name="user", renderer="user.jinja2")
@use_kwargs(PaginatedListingSchema())
@use_kwargs(
    {"post_type": String(load_from="type", validate=OneOf(("topic", "comment")))}
)
def get_user(
    request: Request,
    after: str,
    before: str,
    per_page: int,
    post_type: Optional[str] = None,
) -> dict:
    """Generate the main user history page."""
    user = request.context

    if not request.has_permission("view_types", user):
        post_type = None

    if post_type:
        if post_type == "topic":
            query = request.query(Topic).filter(Topic.user == user)
        elif post_type == "comment":
            query = request.query(Comment).filter(Comment.user == user)

        if before:
            query = query.before_id36(before)

        if after:
            query = query.after_id36(after)

        query = query.join_all_relationships()

        # include removed posts if the user's looking at their own page or is an admin
        if user == request.user or request.user.is_admin:
            query = query.include_removed()

        posts = query.get_page(per_page)
    else:
        posts = _get_user_recent_activity(request, user)

    return {
        "user": user,
        "posts": posts,
        "post_type": post_type,
        "comment_label_options": CommentLabelOption,
    }


@view_config(route_name="invite", renderer="invite.jinja2")
def get_invite(request: Request) -> dict:
    """Generate the invite page."""
    # get any existing unused invite codes
    codes = (
        request.query(UserInviteCode)
        .filter(
            UserInviteCode.user_id == request.user.user_id,
            UserInviteCode.invitee_id == None,  # noqa
        )
        .order_by(desc(UserInviteCode.created_time))
        .all()
    )

    return {"codes": codes}
