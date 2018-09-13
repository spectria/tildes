# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to posting/viewing topics and comments on them."""

from collections import namedtuple
from typing import Any, Optional

from marshmallow import missing, ValidationError
from marshmallow.fields import String
from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy import cast
from sqlalchemy.sql.expression import any_, desc
from sqlalchemy_utils import Ltree
from webargs.pyramidparser import use_kwargs
from zope.sqlalchemy import mark_changed

from tildes.enums import (
    CommentNotificationType,
    CommentSortOption,
    CommentTagOption,
    LogEventType,
    TopicSortOption,
)
from tildes.lib.database import ArrayOfLtree
from tildes.lib.datetime import SimpleHoursPeriod
from tildes.models.comment import Comment, CommentNotification, CommentTree
from tildes.models.group import Group
from tildes.models.log import LogComment, LogTopic
from tildes.models.topic import Topic, TopicVisit
from tildes.models.user import UserGroupSettings
from tildes.schemas.comment import CommentSchema
from tildes.schemas.fields import Enum, ShortTimePeriod
from tildes.schemas.topic import TopicSchema
from tildes.schemas.topic_listing import TopicListingSchema
from tildes.views.decorators import rate_limit_view


DefaultSettings = namedtuple("DefaultSettings", ["order", "period"])


@view_config(route_name="group_topics", request_method="POST", permission="post_topic")
@use_kwargs(TopicSchema(only=("title", "markdown", "link")))
@use_kwargs({"tags": String()})
def post_group_topics(
    request: Request, title: str, markdown: str, link: str, tags: str
) -> HTTPFound:
    """Post a new topic to a group."""
    if link:
        new_topic = Topic.create_link_topic(
            group=request.context, author=request.user, title=title, link=link
        )

        # if they specified both a link and markdown, use the markdown to post an
        # initial comment on the topic
        if markdown:
            new_comment = Comment(
                topic=new_topic, author=request.user, markdown=markdown
            )
            request.db_session.add(new_comment)

            request.db_session.add(
                LogComment(LogEventType.COMMENT_POST, request, new_comment)
            )
    else:
        new_topic = Topic.create_text_topic(
            group=request.context, author=request.user, title=title, markdown=markdown
        )

    try:
        new_topic.tags = tags.split(",")
    except ValidationError:
        raise ValidationError({"tags": ["Invalid tags"]})

    request.apply_rate_limit("topic_post")

    request.db_session.add(new_topic)

    request.db_session.add(LogTopic(LogEventType.TOPIC_POST, request, new_topic))

    # flush the changes to the database so the new topic's ID is generated
    request.db_session.flush()

    raise HTTPFound(location=new_topic.permalink)


@view_config(route_name="home", renderer="home.jinja2")
@view_config(route_name="group", renderer="topic_listing.jinja2")
@use_kwargs(TopicListingSchema())
def get_group_topics(
    request: Request,
    order: Any,  # more specific would be better, but missing isn't typed
    period: Any,  # more specific would be better, but missing isn't typed
    after: str,
    before: str,
    per_page: int,
    rank_start: Optional[int],
    tag: Optional[Ltree],
    unfiltered: bool,
) -> dict:
    """Get a listing of topics in the group."""
    # pylint: disable=too-many-arguments
    if request.matched_route.name == "home":
        # on the home page, include topics from the user's subscribed groups
        groups = [sub.group for sub in request.user.subscriptions]
    else:
        # otherwise, just topics from the single group that we're looking at
        groups = [request.context]

    default_settings = _get_default_settings(request, order)

    if order is missing:
        order = default_settings.order

    if period is missing:
        period = default_settings.period

    # set up the basic query for topics
    query = (
        request.query(Topic)
        .join_all_relationships()
        .inside_groups(groups)
        .apply_sort_option(order)
    )

    # restrict the time period, if not set to "all time"
    if period:
        query = query.inside_time_period(period)

    # restrict to a specific tag, if we're viewing a single one
    if tag:
        query = query.has_tag(tag)

    # apply before/after pagination restrictions if relevant
    if before:
        query = query.before_id36(before)

    if after:
        query = query.after_id36(after)

    # apply topic tag filters unless they're disabled or viewing a single tag
    if not (tag or unfiltered):
        # pylint: disable=protected-access
        query = query.filter(
            ~Topic._tags.descendant_of(  # type: ignore
                any_(cast(request.user._filtered_topic_tags, ArrayOfLtree))
            )
        )

    topics = query.get_page(per_page)

    period_options = [SimpleHoursPeriod(hours) for hours in (1, 12, 24, 72)]

    # add the current period to the bottom of the dropdown if it's not one of the
    # "standard" ones
    if period and period not in period_options:
        period_options.append(period)

    return {
        "group": request.context,
        "topics": topics,
        "order": order,
        "order_options": TopicSortOption,
        "period": period,
        "period_options": period_options,
        "is_default_period": period == default_settings.period,
        "is_default_view": (
            period == default_settings.period and order == default_settings.order
        ),
        "rank_start": rank_start,
        "tag": tag,
        "unfiltered": unfiltered,
    }


@view_config(route_name="search", renderer="search.jinja2")
@use_kwargs(TopicListingSchema(only=("after", "before", "order", "per_page", "period")))
@use_kwargs({"search": String(load_from="q")})
def get_search(
    request: Request,
    order: Any,
    period: Any,
    after: str,
    before: str,
    per_page: int,
    search: str,
) -> dict:
    """Get a list of search results."""
    # pylint: disable=too-many-arguments
    if order is missing:
        order = TopicSortOption.NEW

    if period is missing:
        period = None

    query = (
        request.query(Topic)
        .join_all_relationships()
        .search(search)
        .apply_sort_option(order)
    )

    # restrict the time period, if not set to "all time"
    if period:
        query = query.inside_time_period(period)

    # apply before/after pagination restrictions if relevant
    if before:
        query = query.before_id36(before)

    if after:
        query = query.after_id36(after)

    topics = query.get_page(per_page)

    period_options = [SimpleHoursPeriod(hours) for hours in (1, 12, 24, 72)]

    # add the current period to the bottom of the dropdown if it's not one of the
    # "standard" ones
    if period and period not in period_options:
        period_options.append(period)

    return {
        "search": search,
        "topics": topics,
        "order": order,
        "order_options": TopicSortOption,
        "period": period,
        "period_options": period_options,
    }


@view_config(
    route_name="new_topic", renderer="new_topic.jinja2", permission="post_topic"
)
def get_new_topic_form(request: Request) -> dict:
    """Form for entering a new topic to post."""
    group = request.context

    return {"group": group}


@view_config(route_name="topic", renderer="topic.jinja2")
@use_kwargs({"comment_order": Enum(CommentSortOption, missing="votes")})
def get_topic(request: Request, comment_order: CommentSortOption) -> dict:
    """View a single topic."""
    topic = request.context

    # deleted and removed comments need to be included since they're necessary for
    # building the tree if they have replies
    comments = (
        request.query(Comment)
        .include_deleted()
        .include_removed()
        .filter(Comment.topic == topic)
        .order_by(Comment.created_time)
        .all()
    )
    tree = CommentTree(comments, comment_order, request.user)

    # check if there are any items in the log to show
    visible_events = (
        LogEventType.TOPIC_LOCK,
        LogEventType.TOPIC_MOVE,
        LogEventType.TOPIC_REMOVE,
        LogEventType.TOPIC_TAG,
        LogEventType.TOPIC_TITLE_EDIT,
        LogEventType.TOPIC_UNLOCK,
        LogEventType.TOPIC_UNREMOVE,
    )
    log = (
        request.query(LogTopic)
        .filter(LogTopic.topic == topic, LogTopic.event_type.in_(visible_events))
        .order_by(desc(LogTopic.event_time))
        .all()
    )

    tree.collapse_from_tags()

    # if the user has the "mark new comments" feature enabled
    if request.user and request.user.track_comment_visits:
        # update their last visit time for this topic
        statement = TopicVisit.generate_insert_statement(request.user, topic)
        request.db_session.execute(statement)
        mark_changed(request.db_session)

        # collapse old comments if the user has a previous visit to the topic
        # (and doesn't have that behavior disabled)
        if topic.last_visit_time and request.user.collapse_old_comments:
            tree.uncollapse_new_comments(topic.last_visit_time)
            tree.finalize_collapsing_maximized()

    return {
        "topic": topic,
        "log": log,
        "comments": tree,
        "comment_order": comment_order,
        "comment_order_options": CommentSortOption,
        "comment_tag_options": CommentTagOption,
    }


@view_config(route_name="topic", request_method="POST", permission="comment")
@use_kwargs(CommentSchema(only=("markdown",)))
@rate_limit_view("comment_post")
def post_comment_on_topic(request: Request, markdown: str) -> HTTPFound:
    """Post a new top-level comment on a topic."""
    topic = request.context

    new_comment = Comment(topic=topic, author=request.user, markdown=markdown)
    request.db_session.add(new_comment)

    request.db_session.add(LogComment(LogEventType.COMMENT_POST, request, new_comment))

    if topic.user != request.user and not topic.is_deleted:
        notification = CommentNotification(
            topic.user, new_comment, CommentNotificationType.TOPIC_REPLY
        )
        request.db_session.add(notification)

    raise HTTPFound(location=topic.permalink)


def _get_default_settings(request: Request, order: Any) -> DefaultSettings:
    if isinstance(request.context, Group):
        is_home_page = False
        user_settings = (
            request.query(UserGroupSettings)
            .filter(
                UserGroupSettings.user == request.user,
                UserGroupSettings.group == request.context,
            )
            .one_or_none()
        )
    else:
        is_home_page = True
        user_settings = None

    if user_settings and user_settings.default_order:
        default_order = user_settings.default_order
    elif request.user.home_default_order:
        default_order = request.user.home_default_order
    else:
        default_order = TopicSortOption.ACTIVITY

    # the default period depends on what the order is, so we need to see if we're going
    # to end up using the default order here as well
    if order is missing:
        order = default_order

    if user_settings and user_settings.default_period:
        user_default = user_settings.default_period
        default_period = ShortTimePeriod().deserialize(user_default)
    elif request.user.home_default_period:
        user_default = request.user.home_default_period
        default_period = ShortTimePeriod().deserialize(user_default)
    else:
        # Overall default periods, if the user doesn't have either a group-specific or a
        # home default set up:
        #   * "all time" if sorting by new
        #   * "all time" if sorting by activity and inside a group
        #   * "3 days" if sorting by activity and on home page
        #   * "1 day" otherwise (sorting by most votes or most comments)
        if order == TopicSortOption.NEW:
            default_period = None
        elif order == TopicSortOption.ACTIVITY and not is_home_page:
            default_period = None
        elif order == TopicSortOption.ACTIVITY:
            default_period = SimpleHoursPeriod(72)
        else:
            default_period = SimpleHoursPeriod(24)

    return DefaultSettings(order=default_order, period=default_period)
