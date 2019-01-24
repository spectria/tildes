# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to a specific user."""

from typing import List, Optional, Type, Union

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql.expression import desc
from webargs.pyramidparser import use_kwargs

from tildes.enums import CommentLabelOption
from tildes.models.comment import Comment
from tildes.models.pagination import MixedPaginatedResults
from tildes.models.topic import Topic
from tildes.models.user import UserInviteCode
from tildes.schemas.fields import PostType
from tildes.schemas.listing import MixedListingSchema


@view_config(route_name="user", renderer="user.jinja2")
@use_kwargs(MixedListingSchema())
@use_kwargs({"post_type": PostType(load_from="type")})
def get_user(
    request: Request,
    after: Optional[str],
    before: Optional[str],
    per_page: int,
    anchor_type: Optional[str],
    post_type: Optional[str] = None,
) -> dict:
    # pylint: disable=too-many-arguments
    """Generate the main user history page."""
    user = request.context

    if not request.has_permission("view_history", user):
        post_type = None
        after = None
        before = None
        anchor_type = None
        per_page = 20

    types_to_query: List[Union[Type[Topic], Type[Comment]]]
    if post_type == "topic":
        types_to_query = [Topic]
    elif post_type == "comment":
        types_to_query = [Comment]
    else:
        # the order here is important so items are in the right order when the results
        # are merged at the end (we want topics to come first when times match)
        types_to_query = [Comment, Topic]

    result_sets = []
    for type_to_query in types_to_query:
        query = request.query(type_to_query).filter(type_to_query.user == user)

        if anchor_type:
            query = query.anchor_type(anchor_type)

        if before:
            query = query.before_id36(before)

        if after:
            query = query.after_id36(after)

        query = query.join_all_relationships()

        # include removed posts if the user's looking at their own page or is an admin
        if user == request.user or request.user.is_admin:
            query = query.include_removed()

        result_sets.append(query.get_page(per_page))

    if len(result_sets) == 1:
        posts = result_sets[0]
    else:
        posts = MixedPaginatedResults(result_sets)

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
