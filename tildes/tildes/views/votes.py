"""Views relating to voted posts."""

from typing import Optional, Type, Union

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql import desc

from tildes.models.comment import Comment, CommentVote
from tildes.models.topic import Topic, TopicVote
from tildes.schemas.fields import PostType
from tildes.schemas.listing import PaginatedListingSchema
from tildes.views.decorators import use_kwargs


@view_config(route_name="votes", renderer="votes.jinja2")
@use_kwargs(PaginatedListingSchema())
@use_kwargs({"post_type": PostType(data_key="type", missing="topic")})
def get_voted_posts(
    request: Request,
    after: Optional[str],
    before: Optional[str],
    per_page: int,
    post_type: str,
) -> dict:
    """Generate the voted posts page."""
    # pylint: disable=unused-argument
    user = request.user

    vote_cls: Union[Type[CommentVote], Type[TopicVote]]

    if post_type == "comment":
        post_cls = Comment
        vote_cls = CommentVote
    elif post_type == "topic":
        post_cls = Topic
        vote_cls = TopicVote

    query = (
        request.query(post_cls).only_user_voted().order_by(desc(vote_cls.created_time))
    )

    if before:
        query = query.before_id36(before)

    if after:
        query = query.after_id36(after)

    query = query.join_all_relationships()

    posts = query.all()

    return {"user": user, "posts": posts, "post_type": post_type}
