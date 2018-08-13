"""Views related to notifications."""

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql.expression import desc

from tildes.enums import CommentTagOption
from tildes.models.comment import CommentNotification


@view_config(route_name="notifications_unread", renderer="notifications_unread.jinja2")
def get_user_unread_notifications(request: Request) -> dict:
    """Show the logged-in user's unread notifications."""
    notifications = (
        request.query(CommentNotification)
        .join_all_relationships()
        .filter(
            CommentNotification.user == request.user,
            CommentNotification.is_unread == True,  # noqa
        )
        .order_by(desc(CommentNotification.created_time))
        .all()
    )

    # if the user has the "automatically mark notifications as read" setting enabled,
    # mark all their notifications as read
    if request.user.auto_mark_notifications_read:
        for notification in notifications:
            notification.is_unread = False

    return {"notifications": notifications, "comment_tag_options": CommentTagOption}


@view_config(route_name="notifications", renderer="notifications.jinja2")
def get_user_notifications(request: Request) -> dict:
    """Show the most recent 100 of the logged-in user's read notifications."""
    notifications = (
        request.query(CommentNotification)
        .join_all_relationships()
        .filter(
            CommentNotification.user == request.user,
            CommentNotification.is_unread == False,  # noqa
        )
        .order_by(desc(CommentNotification.created_time))
        .limit(100)
        .all()
    )

    return {"notifications": notifications, "comment_tag_options": CommentTagOption}
