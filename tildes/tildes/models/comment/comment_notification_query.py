"""Contains the CommentNotificationQuery class."""

from typing import Any

from pyramid.request import Request
from sqlalchemy.orm import joinedload

from tildes.models import ModelQuery
from .comment_notification import CommentNotification
from .comment_vote import CommentVote


class CommentNotificationQuery(ModelQuery):
    """Specialized ModelQuery for CommentNotifications."""

    def __init__(self, request: Request) -> None:
        """Initialize a CommentNotificationQuery for the request."""
        super().__init__(CommentNotification, request)

    def _attach_extra_data(self) -> 'CommentNotificationQuery':
        """Attach the user's comment votes to the query."""
        vote_subquery = (
            self.request.query(CommentVote)
            .filter(
                CommentVote.comment_id == CommentNotification.comment_id,
                CommentVote.user == self.request.user,
            )
            .exists()
            .label('user_voted')
        )
        return self.add_columns(vote_subquery)

    def join_all_relationships(self) -> 'CommentNotificationQuery':
        """Eagerly join the comment, topic, and group to the notification."""
        self = self.options(
            joinedload(CommentNotification.comment)
            .joinedload('topic')
            .joinedload('group')
        )

        return self

    @staticmethod
    def _process_result(result: Any) -> CommentNotification:
        """Merge the user's voting data onto the comment."""
        if isinstance(result, CommentNotification):
            # the result is already a CommentNotification, no merging needed
            notification = result
            notification.comment.user_voted = False
        else:
            notification = result.CommentNotification
            notification.comment.user_voted = result.user_voted

        return notification
