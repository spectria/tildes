# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the CommentQuery class."""

from typing import Any

from pyramid.request import Request

from tildes.models.pagination import PaginatedQuery
from .comment import Comment
from .comment_vote import CommentVote


class CommentQuery(PaginatedQuery):
    """Specialized ModelQuery for Comments."""

    def __init__(self, request: Request) -> None:
        """Initialize a CommentQuery for the request.

        If the user is logged in, additional user-specific data will be fetched along
        with the comments. For the moment, this is whether the user has voted on them.
        """
        super().__init__(Comment, request)

    def _attach_extra_data(self) -> "CommentQuery":
        """Attach the extra user data to the query."""
        if not self.request.user:
            return self

        return self._attach_vote_data()

    def _attach_vote_data(self) -> "CommentQuery":
        """Add a subquery to include whether the user has voted."""
        vote_subquery = (
            self.request.query(CommentVote)
            .filter(
                CommentVote.comment_id == Comment.comment_id,
                CommentVote.user_id == self.request.user.user_id,
            )
            .exists()
            .label("user_voted")
        )
        return self.add_columns(vote_subquery)

    @staticmethod
    def _process_result(result: Any) -> Comment:
        """Merge additional user-context data in result onto the comment."""
        if isinstance(result, Comment):
            # the result is already a Comment, no merging needed
            comment = result
            comment.user_voted = False
        else:
            comment = result.Comment
            comment.user_voted = result.user_voted

        return comment
