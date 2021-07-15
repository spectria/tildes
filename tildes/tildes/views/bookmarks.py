"""Views relating to bookmarks."""

from typing import Optional, Union

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql import desc

from tildes.models.comment import Comment, CommentBookmark
from tildes.models.topic import Topic, TopicBookmark
from tildes.schemas.fields import PostType
from tildes.schemas.listing import PaginatedListingSchema
from tildes.views.decorators import use_kwargs


@view_config(route_name="bookmarks", renderer="bookmarks.jinja2")
@use_kwargs(PaginatedListingSchema())
@use_kwargs({"post_type": PostType(data_key="type", missing="topic")})
def get_bookmarks(
    request: Request,
    after: Optional[str],
    before: Optional[str],
    per_page: int,
    post_type: str,
) -> dict:
    """Generate the bookmarks page."""
    # pylint: disable=unused-argument
    user = request.user

    bookmark_cls: Union[type[CommentBookmark], type[TopicBookmark]]

    if post_type == "comment":
        post_cls = Comment
        bookmark_cls = CommentBookmark
    elif post_type == "topic":
        post_cls = Topic
        bookmark_cls = TopicBookmark

    query = (
        request.query(post_cls)
        .only_bookmarked()
        .order_by(desc(bookmark_cls.created_time))
    )

    if before:
        query = query.before_id36(before)

    if after:
        query = query.after_id36(after)

    query = query.join_all_relationships()

    posts = query.all()

    return {"user": user, "posts": posts, "post_type": post_type}
