# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to posting/viewing topics and comments on them."""

from collections import namedtuple
from datetime import timedelta
from difflib import SequenceMatcher
from typing import Any, Optional, Union

from marshmallow import missing, ValidationError
from marshmallow.fields import Boolean, String
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy import cast
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import any_, desc
from sqlalchemy_utils import Ltree

from tildes.enums import (
    CommentLabelOption,
    CommentNotificationType,
    CommentTreeSortOption,
    LogEventType,
    TopicSortOption,
)
from tildes.lib.database import TagList
from tildes.lib.datetime import SimpleHoursPeriod, utc_now
from tildes.models.comment import Comment, CommentNotification, CommentTree
from tildes.models.group import Group, GroupWikiPage
from tildes.models.log import LogComment, LogTopic
from tildes.models.topic import Topic, TopicSchedule, TopicVisit
from tildes.models.user import UserGroupSettings
from tildes.schemas.comment import CommentSchema
from tildes.schemas.fields import Enum, ShortTimePeriod
from tildes.schemas.listing import TopicListingSchema
from tildes.schemas.topic import TopicSchema
from tildes.views.decorators import rate_limit_view, use_kwargs
from tildes.views.financials import get_financial_data


DefaultSettings = namedtuple("DefaultSettings", ["order", "period"])


@view_config(route_name="group_topics", request_method="POST", permission="topic.post")
@use_kwargs(TopicSchema(only=("title", "markdown", "link")), location="form")
@use_kwargs(
    {"tags": String(missing=""), "confirm_repost": Boolean(missing=False)},
    location="form",
)
def post_group_topics(
    request: Request,
    title: str,
    markdown: str,
    link: str,
    tags: str,
    confirm_repost: bool,
) -> Union[HTTPFound, Response]:
    """Post a new topic to a group."""
    group = request.context

    if link:
        # check to see if this link has already been posted in the last 6 months
        previous_topics = (
            request.query(Topic)
            .filter(
                Topic.link == link,
                Topic.created_time >= utc_now() - timedelta(days=180),
            )
            .order_by(desc(Topic.created_time))
            .limit(5)
            .all()
        )

        if previous_topics and not confirm_repost:
            # Render partial form for Intercooler.js request, whole page for normal POST
            # (I don't like this much, there must be a better way to handle this)
            if "X-IC-Request" in request.headers:
                template = "tildes:templates/includes/new_topic_form.jinja2"
            else:
                template = "tildes:templates/new_topic.jinja2"

            return render_to_response(
                template,
                {
                    "group": group,
                    "title": title,
                    "link": link,
                    "markdown": markdown,
                    "tags": tags,
                    "previous_topics": previous_topics,
                },
                request=request,
            )

        new_topic = Topic.create_link_topic(
            group=group, author=request.user, title=title, link=link
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
            group=group, author=request.user, title=title, markdown=markdown
        )

    try:
        new_topic.tags = tags.split(",")
    except ValidationError as exc:
        raise ValidationError({"tags": ["Invalid tags"]}) from exc

    # remove any tag that's the same as the group's name
    new_topic.tags = [tag for tag in new_topic.tags if tag != str(group.path)]

    request.apply_rate_limit("topic_post")

    request.db_session.add(new_topic)

    request.db_session.add(LogTopic(LogEventType.TOPIC_POST, request, new_topic))

    # if the user added tags to the topic, show the field by default in the future
    if tags and not request.user.show_tags_on_new_topic:
        request.user.show_tags_on_new_topic = True
        request.db_session.add(request.user)

    # flush the changes to the database so the new topic's ID is generated
    request.db_session.flush()

    raise HTTPFound(location=new_topic.permalink)


@view_config(route_name="home", renderer="home.jinja2")
@view_config(route_name="home_atom", renderer="home.atom.jinja2")
@view_config(route_name="home_rss", renderer="home.rss.jinja2")
@view_config(route_name="group", renderer="topic_listing.jinja2")
@view_config(route_name="group_topics_atom", renderer="topic_listing.atom.jinja2")
@view_config(route_name="group_topics_rss", renderer="topic_listing.rss.jinja2")
@use_kwargs(TopicListingSchema())
def get_group_topics(  # noqa
    request: Request,
    after: Optional[str],
    before: Optional[str],
    order: Optional[TopicSortOption],
    per_page: int,
    rank_start: Optional[int],
    tag: Optional[Ltree],
    unfiltered: bool,
    **kwargs: Any
) -> dict:
    """Get a listing of topics in the group."""
    # period needs special treatment so we can distinguish between missing and None
    period = kwargs.get("period", missing)

    is_home_page = request.matched_route.name in ["home", "home_atom", "home_rss"]
    is_atom = request.matched_route.name in ["home_atom", "group_topics_atom"]
    is_rss = request.matched_route.name in ["home_rss", "group_topics_rss"]

    if is_home_page:
        # on the home page, include topics from the user's subscribed groups
        # (or all groups, if logged-out)
        if request.user:
            groups = [sub.group for sub in request.user.subscriptions]
        else:
            groups = [
                group for group in request.query(Group).all() if group.path != "test"
            ]
        subgroups = None
    else:
        # otherwise, just topics from the single group that we're looking at
        groups = [request.context]

        subgroups = (
            request.query(Group)
            .filter(
                Group.path.descendant_of(request.context.path),
                Group.path != request.context.path,
            )
            .all()
        )

    default_settings = _get_default_settings(request, order)

    if not order:
        order = default_settings.order

    if period is missing:
        period = default_settings.period

    # force Newest sort order, and All Time period, for RSS feeds
    if is_atom or is_rss:
        order = TopicSortOption.NEW
        period = None

    # set up the basic query for topics
    query = (
        request.query(Topic)
        .join_all_relationships()
        .inside_groups(groups, include_subgroups=not is_home_page)
        .exclude_ignored()
        .apply_sort_option(order)
    )

    # restrict the time period, if not set to "all time"
    if period:
        query = query.inside_time_period(period)

    # restrict to a specific tag, if we're viewing a single one
    if tag:
        query = query.has_tag(str(tag))

    # apply before/after pagination restrictions if relevant
    if before:
        query = query.before_id36(before)

    if after:
        query = query.after_id36(after)

    # apply topic tag filters unless they're disabled
    if request.user and request.user.filtered_topic_tags and not unfiltered:
        filtered_topic_tags = request.user.filtered_topic_tags

        # if viewing single tag, don't filter that tag and its ancestors
        # for example, if viewing "ask.survey", don't filter "ask.survey" or "ask"
        if tag:
            filtered_topic_tags = [
                ft
                for ft in filtered_topic_tags
                if not tag.descendant_of(ft.replace(" ", "_"))
            ]

        query = query.filter(
            ~Topic.tags.descendant_of(  # type: ignore
                any_(cast(filtered_topic_tags, TagList))
            )
        )

    topics = query.get_page(per_page)

    period_options = [SimpleHoursPeriod(hours) for hours in (1, 12, 24, 72, 168)]

    # add the current period to the bottom of the dropdown if it's not one of the
    # "standard" ones
    if period and period not in period_options:
        period_options.append(period)

    if isinstance(request.context, Group):
        wiki_pages = (
            request.query(GroupWikiPage)
            .filter(GroupWikiPage.group == request.context)
            .order_by(GroupWikiPage.path)
            .all()
        )

        # remove the index from the page list, we'll output it separately
        if any(page.path == "index" for page in wiki_pages):
            wiki_has_index = True
            wiki_pages = [page for page in wiki_pages if page.path != "index"]
        else:
            wiki_has_index = False
    else:
        wiki_pages = None
        wiki_has_index = False

    if isinstance(request.context, Group):
        # Get the most recent topic from each scheduled topic in this group
        group_schedules = (
            request.query(TopicSchedule)
            .options(joinedload(TopicSchedule.latest_topic))
            .filter(
                TopicSchedule.group == request.context,
                TopicSchedule.next_post_time != None,  # noqa
            )
            .order_by(TopicSchedule.next_post_time)
            .all()
        )
        most_recent_scheduled_topics = [
            schedule.latest_topic for schedule in group_schedules
        ]
    else:
        most_recent_scheduled_topics = []

    if is_home_page:
        financial_data = get_financial_data(request.db_session)
    else:
        financial_data = None

    if is_atom:
        request.response.content_type = "application/atom+xml"
    if is_rss:
        request.response.content_type = "application/rss+xml"

    return {
        "group": request.context,
        "groups": groups,
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
        "wiki_pages": wiki_pages,
        "wiki_has_index": wiki_has_index,
        "subgroups": subgroups,
        "most_recent_scheduled_topics": most_recent_scheduled_topics,
        "financial_data": financial_data,
        "current_time": utc_now(),
    }


@view_config(route_name="search", renderer="search.jinja2")
@view_config(route_name="group_search", renderer="search.jinja2")
@use_kwargs(TopicListingSchema(only=("after", "before", "order", "per_page", "period")))
@use_kwargs({"search": String(data_key="q", missing="")})
def get_search(
    request: Request,
    order: Optional[TopicSortOption],
    after: Optional[str],
    before: Optional[str],
    per_page: int,
    search: str,
    **kwargs: Any
) -> dict:
    """Get a list of search results."""
    # period needs special treatment so we can distinguish between missing and None
    period = kwargs.get("period", missing)

    group = None
    if isinstance(request.context, Group):
        group = request.context

    if not order:
        order = TopicSortOption.NEW

    if period is missing:
        period = None

    query = (
        request.query(Topic)
        .join_all_relationships()
        .search(search)
        .apply_sort_option(order)
    )

    # if searching from inside a group, restrict to that group alone
    if group:
        query = query.inside_groups([group])

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
        "group": group,
        "order": order,
        "order_options": TopicSortOption,
        "period": period,
        "period_options": period_options,
    }


@view_config(
    route_name="new_topic", renderer="new_topic.jinja2", permission="topic.post"
)
@use_kwargs({"title": String(missing=""), "link": String(missing="")})
def get_new_topic_form(request: Request, title: str, link: str) -> dict:
    """Form for entering a new topic to post."""
    group = request.context

    return {"group": group, "title": title, "link": link}


@view_config(route_name="topic", renderer="topic.jinja2")
@view_config(route_name="topic_no_title", renderer="topic.jinja2")
@use_kwargs({"comment_order": Enum(CommentTreeSortOption, missing=None)})
def get_topic(request: Request, comment_order: CommentTreeSortOption) -> dict:
    """View a single topic."""
    topic = request.context
    if comment_order is None:
        if request.user and request.user.comment_sort_order_default:
            comment_order = request.user.comment_sort_order_default
        else:
            comment_order = CommentTreeSortOption.RELEVANCE

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

    # check for link information (content metadata) to display
    if topic.is_link_type:
        content_metadata = topic.content_metadata_fields_for_display.copy()

        fields_to_hide = ("Domain", "Description")
        for field in fields_to_hide:
            content_metadata.pop(field, None)

        # don't include the title if it's pretty similar to the topic's title
        if "Title" in content_metadata:
            similarity = SequenceMatcher(a=content_metadata["Title"], b=topic.title)
            if similarity.ratio() >= 0.6:
                del content_metadata["Title"]
    else:
        content_metadata = None

    # check if there are any items in the log to show
    visible_events = (
        LogEventType.TOPIC_LINK_EDIT,
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

    tree.collapse_from_labels()

    if request.user:
        request.db_session.add(TopicVisit(request.user, topic))

        # collapse old comments if the user has a previous visit to the topic
        # (and doesn't have that behavior disabled)
        if topic.last_visit_time and request.user.collapse_old_comments:
            tree.uncollapse_new_comments(topic.last_visit_time)
            tree.finalize_collapsing_maximized()

    return {
        "topic": topic,
        "content_metadata": content_metadata,
        "log": log,
        "comments": tree,
        "comment_order": comment_order,
        "comment_order_options": CommentTreeSortOption,
        "comment_label_options": CommentLabelOption,
    }


@view_config(route_name="topic", request_method="POST", permission="comment")
@use_kwargs(CommentSchema(only=("markdown",)), location="form")
@rate_limit_view("comment_post")
def post_comment_on_topic(request: Request, markdown: str) -> HTTPFound:
    """Post a new top-level comment on a topic."""
    topic = request.context

    new_comment = Comment(topic=topic, author=request.user, markdown=markdown)
    request.db_session.add(new_comment)

    request.db_session.add(LogComment(LogEventType.COMMENT_POST, request, new_comment))

    if CommentNotification.should_create_reply_notification(new_comment):
        notification = CommentNotification(
            topic.user, new_comment, CommentNotificationType.TOPIC_REPLY
        )
        request.db_session.add(notification)

    raise HTTPFound(location=topic.permalink)


def _get_default_settings(
    request: Request, order: Optional[TopicSortOption]
) -> DefaultSettings:
    if isinstance(request.context, Group) and request.user:
        user_settings = (
            request.query(UserGroupSettings)
            .filter(
                UserGroupSettings.user == request.user,
                UserGroupSettings.group == request.context,
            )
            .one_or_none()
        )
    else:
        user_settings = None

    if user_settings and user_settings.default_order:
        default_order = user_settings.default_order
    elif request.user and request.user.home_default_order:
        default_order = request.user.home_default_order
    else:
        default_order = TopicSortOption.ACTIVITY

    # the default period depends on what the order is, so we need to see if we're going
    # to end up using the default order here as well
    if not order:
        order = default_order

    if user_settings and user_settings.default_period:
        user_default = user_settings.default_period
        default_period = ShortTimePeriod().deserialize(user_default)
    elif request.user and request.user.home_default_period:
        user_default = request.user.home_default_period
        default_period = ShortTimePeriod().deserialize(user_default)
    else:
        # Overall default periods, if the user doesn't have either a group-specific or a
        # home default set up:
        #   * "1 day" if sorting by most votes or most comments
        #   * "all time" otherwise
        if order in (TopicSortOption.VOTES, TopicSortOption.COMMENTS):
            default_period = SimpleHoursPeriod(24)
        else:
            default_period = None

    return DefaultSettings(order=default_order, period=default_period)
