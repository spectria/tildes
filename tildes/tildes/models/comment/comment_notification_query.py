# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the CommentNotificationQuery class."""

from typing import Any

from pyramid.request import Request
from sqlalchemy.orm import joinedload

from tildes.lib.id import id_to_id36
from tildes.models.pagination import PaginatedQuery, PaginatedResults

from .comment_notification import CommentNotification
from .comment_vote import CommentVote


class CommentNotificationQuery(PaginatedQuery):
    """Specialized query class for CommentNotifications."""

    def __init__(self, request: Request):
        """Initialize a CommentNotificationQuery for the request."""
        super().__init__(CommentNotification, request)

    def _anchor_subquery(self, anchor_id: int) -> Any:
        return (
            self.request.db_session.query(*self.sorting_columns)
            .filter(
                CommentNotification.user == self.request.user,
                CommentNotification.comment_id == anchor_id,
            )
            .subquery()
        )

    def _attach_extra_data(self) -> "CommentNotificationQuery":
        """Attach the user's comment votes to the query."""
        vote_subquery = (
            self.request.query(CommentVote)
            .filter(
                CommentVote.comment_id == CommentNotification.comment_id,
                CommentVote.user == self.request.user,
            )
            .exists()
            .label("user_voted")
        )
        return self.add_columns(vote_subquery)

    def join_all_relationships(self) -> "CommentNotificationQuery":
        """Eagerly join the comment, topic, and group to the notification."""
        # pylint: disable=self-cls-assignment
        self = self.options(
            joinedload(CommentNotification.comment)
            .joinedload("topic")
            .joinedload("group")
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

    def get_page(self, per_page: int) -> "CommentNotificationResults":
        """Get a page worth of results from the query (`per page` items)."""
        return CommentNotificationResults(self, per_page)


class CommentNotificationResults(PaginatedResults):
    """Specialized results class for CommentNotifications."""

    @property
    def next_page_after_id36(self) -> str:
        """Return "after" ID36 that should be used to fetch the next page."""
        if not self.has_next_page:
            raise AttributeError

        return id_to_id36(self.results[-1].comment_id)

    @property
    def prev_page_before_id36(self) -> str:
        """Return "before" ID36 that should be used to fetch the prev page."""
        if not self.has_prev_page:
            raise AttributeError

        return id_to_id36(self.results[0].comment_id)
