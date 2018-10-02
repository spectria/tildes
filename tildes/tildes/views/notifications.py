# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to notifications."""

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql.expression import desc
from webargs.pyramidparser import use_kwargs

from tildes.enums import CommentLabelOption
from tildes.models.comment import CommentNotification
from tildes.schemas.listing import PaginatedListingSchema


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

    return {"notifications": notifications, "comment_label_options": CommentLabelOption}


@view_config(route_name="notifications", renderer="notifications.jinja2")
@use_kwargs(PaginatedListingSchema())
def get_user_notifications(
    request: Request, after: str, before: str, per_page: int
) -> dict:
    """Show the logged-in user's previously-read notifications."""
    query = (
        request.query(CommentNotification)
        .join_all_relationships()
        .filter(
            CommentNotification.user == request.user,
            CommentNotification.is_unread == False,  # noqa
        )
        .order_by(desc(CommentNotification.created_time))
    )

    if before:
        query = query.before_id36(before)

    if after:
        query = query.after_id36(after)

    notifications = query.get_page(per_page)

    return {"notifications": notifications, "comment_label_options": CommentLabelOption}
