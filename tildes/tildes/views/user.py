"""Views related to a specific user."""

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql.expression import desc

from tildes.models.comment import Comment
from tildes.models.topic import Topic
from tildes.models.user import UserInviteCode


@view_config(route_name='user', renderer='user.jinja2')
def get_user(request: Request) -> dict:
    """Generate the main user info page."""
    user = request.context

    page_size = 20

    # Since we don't know how many comments or topics will be needed to make
    # up a page, we'll fetch the full page size of both types, merge them,
    # and then trim down to the size afterwards
    query = (
        request.query(Comment)
        .filter(Comment.user == user)
        .order_by(desc(Comment.created_time))
        .limit(page_size)
        .join_all_relationships()
    )

    # include removed comments if the user's looking at their own page
    if user == request.user:
        query = query.include_removed()

    comments = query.all()

    query = (
        request.query(Topic)
        .filter(Topic.user == user)
        .order_by(desc(Topic.created_time))
        .limit(page_size)
        .join_all_relationships()
    )

    # include removed topics if the user's looking at their own page
    if user == request.user:
        query = query.include_removed()

    topics = query.all()

    merged_posts = sorted(
        topics + comments,
        key=lambda post: post.created_time,
        reverse=True,
    )
    merged_posts = merged_posts[:page_size]

    return {
        'user': user,
        'merged_posts': merged_posts,
    }


@view_config(route_name='invite', renderer='invite.jinja2')
def get_invite(request: Request) -> dict:
    """Generate the invite page."""
    # get any existing unused invite codes
    codes = (
        request.query(UserInviteCode)
        .filter(
            UserInviteCode.user_id == request.user.user_id,
            UserInviteCode.invitee_id == None,  # noqa
        )
        .all()
    )

    return {'codes': codes}
