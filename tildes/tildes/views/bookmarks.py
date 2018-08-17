"""Views relating to bookmarks."""

from typing import Optional, Type, Union

from marshmallow.fields import String
from marshmallow.validate import OneOf
from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql import exists, desc
from sqlalchemy.sql.expression import and_
from webargs.pyramidparser import use_kwargs

from tildes.models.comment import Comment, CommentBookmark
from tildes.models.topic import Topic, TopicBookmark
from tildes.schemas.listing import PaginatedListingSchema


@view_config(route_name="bookmarks", renderer="bookmarks.jinja2")
@use_kwargs(PaginatedListingSchema)
@use_kwargs(
    {"post_type": String(load_from="type", validate=OneOf(("topic", "comment")))}
)
def get_bookmarks(
    request: Request,
    after: str,
    before: str,
    per_page: int,
    post_type: Optional[str] = None,
) -> dict:
    """Generate the bookmarks page."""
    user = request.user

    bookmark_cls: Union[Type[CommentBookmark], Type[TopicBookmark]]

    if post_type == "comment":
        post_cls = Comment
        bookmark_cls = CommentBookmark
    else:
        post_cls = Topic
        bookmark_cls = TopicBookmark

    query = (
        request.query(post_cls)
        .filter(
            exists()
            .where(
                and_(
                    bookmark_cls.user == user,
                    bookmark_cls.topic_id == post_cls.topic_id
                    if post_cls == Topic
                    else bookmark_cls.comment_id == post_cls.comment_id,
                )
            )
            .correlate(bookmark_cls)
        )
        .order_by(desc(bookmark_cls.created_time))
    )

    if before:
        query = query.before_id36(before)

    if after:
        query = query.after_id36(after)

    query = query.join_all_relationships()

    posts = query.get_page(per_page)

    return {"user": user, "posts": posts, "post_type": post_type}
