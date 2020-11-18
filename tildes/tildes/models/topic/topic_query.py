# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the TopicQuery class."""

from __future__ import annotations
from typing import Any, Sequence

from pyramid.request import Request
from sqlalchemy import func
from sqlalchemy.sql.expression import and_, desc, label, text

from tildes.enums import TopicSortOption
from tildes.lib.datetime import SimpleHoursPeriod, utc_now
from tildes.models.group import Group
from tildes.models.pagination import PaginatedQuery

from .topic import Topic
from .topic_bookmark import TopicBookmark
from .topic_ignore import TopicIgnore
from .topic_visit import TopicVisit
from .topic_vote import TopicVote


class TopicQuery(PaginatedQuery):
    """Specialized query class for Topics."""

    def __init__(self, request: Request):
        """Initialize a TopicQuery for the request.

        If the user is logged in, additional user-specific data will be fetched along
        with the topics. For the moment, this is whether the user has voted on the
        topics, and data related to their last visit - what time they last visited, and
        how many new comments have been posted since.
        """
        super().__init__(Topic, request)

        self._only_bookmarked = False
        self._only_ignored = False
        self._only_user_voted = False

        self.filter_ignored = False

    def _attach_extra_data(self) -> TopicQuery:
        """Attach the extra user data to the query."""
        if not self.request.user:
            return self

        # pylint: disable=protected-access
        return (
            self._attach_vote_data()
            ._attach_visit_data()
            ._attach_bookmark_data()
            ._attach_ignored_data()
        )

    def _finalize(self) -> TopicQuery:
        """Finalize the query before it's executed."""
        # pylint: disable=self-cls-assignment
        self = super()._finalize()

        if self.filter_ignored and self.request.user:
            self = self.filter(TopicIgnore.topic_id == None)  # noqa

        return self

    def _attach_vote_data(self) -> TopicQuery:
        """Join the data related to whether the user has voted on the topic."""
        query = self.join(
            TopicVote,
            and_(
                TopicVote.topic_id == Topic.topic_id,
                TopicVote.user == self.request.user,
            ),
            isouter=(not self._only_user_voted),
        )
        query = query.add_columns(label("voted_time", TopicVote.created_time))

        return query

    def _attach_bookmark_data(self) -> TopicQuery:
        """Join the data related to whether the user has bookmarked the topic."""
        query = self.join(
            TopicBookmark,
            and_(
                TopicBookmark.topic_id == Topic.topic_id,
                TopicBookmark.user == self.request.user,
            ),
            isouter=(not self._only_bookmarked),
        )
        query = query.add_columns(label("bookmarked_time", TopicBookmark.created_time))

        return query

    def _attach_visit_data(self) -> TopicQuery:
        """Join the data related to the user's last visit to the topic(s)."""
        # subquery using LATERAL to select only the newest visit for each topic
        lateral_subquery = (
            self.request.db_session.query(
                TopicVisit.visit_time, TopicVisit.num_comments
            )
            .filter(
                TopicVisit.topic_id == Topic.topic_id,
                TopicVisit.user == self.request.user,
            )
            .order_by(desc(TopicVisit.visit_time))
            .limit(1)
            .correlate(Topic)
            .subquery()
            .lateral()
        )

        # join on "true" since the subquery already restricts to the row we want
        query = self.outerjoin(lateral_subquery, text("true"))

        query = query.add_columns(lateral_subquery)

        return query

    def _attach_ignored_data(self) -> TopicQuery:
        """Join the data related to whether the user has ignored the topic."""
        query = self.join(
            TopicIgnore,
            and_(
                TopicIgnore.topic_id == Topic.topic_id,
                TopicIgnore.user == self.request.user,
            ),
            isouter=(not self._only_ignored),
        )
        query = query.add_columns(label("ignored_time", TopicIgnore.created_time))

        return query

    @staticmethod
    def _process_result(result: Any) -> Topic:
        """Merge additional user-context data in result onto the topic."""
        if isinstance(result, Topic):
            # the result is already a Topic, no merging needed
            topic = result
            topic.user_voted = False
            topic.bookmark_created_time = None
            topic.last_visit_time = None
            topic.comments_since_last_visit = None
            topic.user_ignored = False
        else:
            topic = result.Topic

            topic.user_voted = bool(result.voted_time)
            topic.user_bookmarked = bool(result.bookmarked_time)
            topic.user_ignored = bool(result.ignored_time)

            topic.last_visit_time = result.visit_time

            topic.comments_since_last_visit = None
            if result.num_comments is not None:
                new_comments = topic.num_comments - result.num_comments
                # prevent showing negative "new comments" due to deletions
                topic.comments_since_last_visit = max(new_comments, 0)

        return topic

    def apply_sort_option(
        self, sort: TopicSortOption, is_desc: bool = True
    ) -> TopicQuery:
        """Apply a TopicSortOption sorting method (generative)."""
        if sort == TopicSortOption.VOTES:
            self._sort_column = Topic.num_votes
        elif sort == TopicSortOption.COMMENTS:
            self._sort_column = Topic.num_comments
        elif sort == TopicSortOption.NEW:
            self._sort_column = Topic.created_time
        elif sort == TopicSortOption.ACTIVITY:
            self._sort_column = Topic.last_interesting_activity_time
        elif sort == TopicSortOption.ALL_ACTIVITY:
            self._sort_column = Topic.last_activity_time

        self.sort_desc = is_desc

        return self

    def inside_groups(
        self, groups: Sequence[Group], include_subgroups: bool = True
    ) -> TopicQuery:
        """Restrict the topics to inside specific groups (generative)."""
        if include_subgroups:
            query_paths = [group.path for group in groups]
            group_ids = self.request.db_session.query(Group.group_id).filter(
                Group.path.descendant_of(query_paths)
            )
        else:
            group_ids = [group.group_id for group in groups]

        return self.filter(Topic.group_id.in_(group_ids))  # type: ignore

    def inside_time_period(self, period: SimpleHoursPeriod) -> TopicQuery:
        """Restrict the topics to inside a time period (generative)."""
        # if the time period is too long, this will crash by creating a datetime outside
        # the valid range - catch that and just don't filter by time period at all if
        # the range is that large
        try:
            start_time = utc_now() - period.timedelta
        except OverflowError:
            return self

        return self.filter(Topic.created_time > start_time)

    def has_tag(self, tag: str) -> TopicQuery:
        """Restrict the topics to ones with a specific tag (generative).

        Note that this method searches for topics that have any tag that contains
        the specified tag as a subpath, not only exact/full matches.
        """
        query = f"*.{tag}.*"

        # pylint: disable=protected-access
        return self.filter(Topic.tags.lquery(query))  # type: ignore

    def search(self, query: str) -> TopicQuery:
        """Restrict the topics to ones that match a search query (generative)."""
        # Replace "." with space, since tags are stored as space-separated strings
        # in the search index.
        # URL domains are not indexed, so removing "." is okay for now.
        query = query.replace(".", " ")

        return self.filter(Topic.search_tsv.op("@@")(func.websearch_to_tsquery(query)))

    def only_bookmarked(self) -> TopicQuery:
        """Restrict the topics to ones that the user has bookmarked (generative)."""
        self._only_bookmarked = True
        return self

    def only_user_voted(self) -> TopicQuery:
        """Restrict the topics to ones that the user has voted on (generative)."""
        self._only_user_voted = True
        return self

    def only_ignored(self) -> TopicQuery:
        """Restrict the topics to ones that the user has ignored (generative)."""
        # pylint: disable=self-cls-assignment
        self._only_ignored = True

        return self

    def exclude_ignored(self) -> TopicQuery:
        """Specify that ignored topics should be excluded (generative)."""
        self.filter_ignored = True

        return self
