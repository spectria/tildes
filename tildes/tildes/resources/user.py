"""Root factories for users."""

from pyramid.request import Request
from webargs.pyramidparser import use_kwargs

from tildes.models.user import User
from tildes.resources import get_resource
from tildes.schemas.user import UserSchema


@use_kwargs(
    UserSchema(only=('username',)),
    locations=('matchdict',),
)
def user_by_username(request: Request, username: str) -> User:
    """Get a user specified by {username} in the route or 404 if not found."""
    query = request.query(User).filter(User.username == username)

    return get_resource(request, query)
