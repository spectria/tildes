"""Root factories for comments."""

from pyramid.request import Request
from webargs.pyramidparser import use_kwargs

from tildes.lib.id import id36_to_id
from tildes.models.comment import Comment
from tildes.resources import get_resource
from tildes.schemas.comment import CommentSchema


@use_kwargs(
    CommentSchema(only=('comment_id36',)),
    locations=('matchdict',),
)
def comment_by_id36(request: Request, comment_id36: str) -> Comment:
    """Get a comment specified by {comment_id36} in the route (or 404)."""
    comment_id = id36_to_id(comment_id36)
    query = request.query(Comment).filter_by(comment_id=comment_id)

    return get_resource(request, query)
