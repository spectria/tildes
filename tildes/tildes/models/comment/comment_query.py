# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the CommentQuery class."""

from typing import Any

from pyramid.request import Request
from sqlalchemy.sql.expression import and_

from tildes.enums import CommentSortOption
from tildes.models.pagination import PaginatedQuery

from .comment import Comment
from .comment_bookmark import CommentBookmark
from .comment_vote import CommentVote


class CommentQuery(PaginatedQuery):
    """Specialized ModelQuery for Comments."""

    def __init__(self, request: Request):
        """Initialize a CommentQuery for the request.

        If the user is logged in, additional user-specific data will be fetched along
        with the comments. For the moment, this is whether the user has voted on them.
        """
        super().__init__(Comment, request)

        self._only_bookmarked = False

    def _attach_extra_data(self) -> "CommentQuery":
        """Attach the extra user data to the query."""
        # pylint: disable=protected-access
        if not self.request.user:
            return self

        return self._attach_vote_data()._attach_bookmark_data()

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

    def _attach_bookmark_data(self) -> "CommentQuery":
        """Join the data related to whether the user has bookmarked the comment."""
        query = self.join(
            CommentBookmark,
            and_(
                CommentBookmark.comment_id == Comment.comment_id,
                CommentBookmark.user == self.request.user,
            ),
            isouter=(not self._only_bookmarked),
        )
        query = query.add_columns(CommentBookmark.created_time)

        return query

    @staticmethod
    def _process_result(result: Any) -> Comment:
        """Merge additional user-context data in result onto the comment."""
        if isinstance(result, Comment):
            # the result is already a Comment, no merging needed
            comment = result
            comment.user_voted = False
            comment.bookmark_created_time = None
        else:
            comment = result.Comment
            comment.user_voted = result.user_voted

            comment.bookmark_created_time = result.created_time

        return comment

    def apply_sort_option(
        self, sort: CommentSortOption, desc: bool = True
    ) -> "CommentQuery":
        """Apply a CommentSortOption sorting method (generative)."""
        if sort == CommentSortOption.VOTES:
            self._sort_column = Comment.num_votes
        elif sort == CommentSortOption.NEW:
            self._sort_column = Comment.created_time

        self.sort_desc = desc

        return self

    def only_bookmarked(self) -> "CommentQuery":
        """Restrict the comments to ones that the user has bookmarked (generative)."""
        self._only_bookmarked = True
        return self
