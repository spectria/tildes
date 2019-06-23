# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Web API endpoints related to comments."""

from marshmallow.fields import Boolean
from pyramid.httpexceptions import HTTPUnprocessableEntity
from pyramid.request import Request
from pyramid.response import Response
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import FlushError
from webargs.pyramidparser import use_kwargs
from zope.sqlalchemy import mark_changed

from tildes.enums import CommentLabelOption, CommentNotificationType, LogEventType
from tildes.lib.datetime import utc_now
from tildes.models.comment import (
    Comment,
    CommentBookmark,
    CommentLabel,
    CommentNotification,
    CommentVote,
)
from tildes.models.log import LogComment
from tildes.models.topic import TopicVisit
from tildes.schemas.comment import CommentLabelSchema, CommentSchema
from tildes.views import IC_NOOP
from tildes.views.decorators import ic_view_config, rate_limit_view


def _mark_comment_read_from_interaction(request: Request, comment: Comment) -> None:
    """Mark any notifications from the comment read due to an interaction.

    Does nothing if the user doesn't have the relevant user preference enabled.
    """
    if not request.user.interact_mark_notifications_read:
        return

    with request.db_session.no_autoflush:
        request.query(CommentNotification).filter(
            CommentNotification.user == request.user,
            CommentNotification.comment == comment,
            CommentNotification.is_unread == True,  # noqa
        ).update({"is_unread": False}, synchronize_session=False)
        _increment_topic_comments_seen(request, comment)


def _increment_topic_comments_seen(request: Request, comment: Comment) -> None:
    """Increment the number of comments in a topic the user has viewed.

    If the user has the "track comment visits" feature enabled, we want to increment the
    number of comments they've seen in the thread that the comment came from, so that
    they don't *both* get a notification as well as have the thread highlight with "(1
    new)". This should only happen if their last visit was before the comment was
    posted, however.  Below, this is implemented as a INSERT ... ON CONFLICT DO UPDATE
    so that it will insert a new topic visit with 1 comment if they didn't previously
    have one at all.
    """
    if request.user.track_comment_visits:
        statement = (
            insert(TopicVisit.__table__)
            .values(
                user_id=request.user.user_id,
                topic_id=comment.topic_id,
                visit_time=utc_now(),
                num_comments=1,
            )
            .on_conflict_do_update(
                constraint=TopicVisit.__table__.primary_key,
                set_={"num_comments": TopicVisit.num_comments + 1},
                where=TopicVisit.visit_time < comment.created_time,
            )
        )

        request.db_session.execute(statement)
        mark_changed(request.db_session)


@ic_view_config(
    route_name="topic_comments",
    request_method="POST",
    renderer="single_comment.jinja2",
    permission="comment",
)
@use_kwargs(CommentSchema(only=("markdown",)))
@rate_limit_view("comment_post")
def post_toplevel_comment(request: Request, markdown: str) -> dict:
    """Post a new top-level comment on a topic with Intercooler."""
    topic = request.context

    new_comment = Comment(topic=topic, author=request.user, markdown=markdown)
    request.db_session.add(new_comment)

    request.db_session.add(LogComment(LogEventType.COMMENT_POST, request, new_comment))

    if topic.user != request.user and not topic.is_deleted:
        notification = CommentNotification(
            topic.user, new_comment, CommentNotificationType.TOPIC_REPLY
        )
        request.db_session.add(notification)

    # commit and then re-query the new comment to get complete data
    request.tm.commit()

    new_comment = (
        request.query(Comment)
        .join_all_relationships()
        .filter_by(comment_id=new_comment.comment_id)
        .one()
    )

    return {"comment": new_comment, "topic": topic}


@ic_view_config(
    route_name="comment_replies",
    request_method="POST",
    renderer="single_comment.jinja2",
    permission="reply",
)
@use_kwargs(CommentSchema(only=("markdown",)))
@rate_limit_view("comment_post")
def post_comment_reply(request: Request, markdown: str) -> dict:
    """Post a reply to a comment with Intercooler."""
    parent_comment = request.context
    new_comment = Comment(
        topic=parent_comment.topic,
        author=request.user,
        markdown=markdown,
        parent_comment=parent_comment,
    )
    request.db_session.add(new_comment)

    request.db_session.add(LogComment(LogEventType.COMMENT_POST, request, new_comment))

    if parent_comment.user != request.user:
        notification = CommentNotification(
            parent_comment.user, new_comment, CommentNotificationType.COMMENT_REPLY
        )
        request.db_session.add(notification)

    _mark_comment_read_from_interaction(request, parent_comment)

    # commit and then re-query the new comment to get complete data
    request.tm.commit()

    new_comment = (
        request.query(Comment)
        .join_all_relationships()
        .filter_by(comment_id=new_comment.comment_id)
        .one()
    )

    return {"comment": new_comment}


@ic_view_config(
    route_name="comment",
    request_method="GET",
    renderer="comment_contents.jinja2",
    permission="view",
)
def get_comment_contents(request: Request) -> dict:
    """Get a comment's body with Intercooler."""
    return {"comment": request.context}


@ic_view_config(
    route_name="comment",
    request_method="GET",
    request_param="ic-trigger-name=edit",
    renderer="comment_edit.jinja2",
    permission="edit",
)
def get_comment_edit(request: Request) -> dict:
    """Get the edit form for a comment with Intercooler."""
    return {"comment": request.context}


@ic_view_config(
    route_name="comment",
    request_method="PATCH",
    renderer="comment_contents.jinja2",
    permission="edit",
)
@use_kwargs(CommentSchema(only=("markdown",)))
def patch_comment(request: Request, markdown: str) -> dict:
    """Update a comment with Intercooler."""
    comment = request.context

    comment.markdown = markdown

    return {"comment": comment}


@ic_view_config(
    route_name="comment",
    request_method="DELETE",
    renderer="comment_contents.jinja2",
    permission="delete",
)
def delete_comment(request: Request) -> dict:
    """Delete a comment with Intercooler."""
    comment = request.context
    comment.is_deleted = True

    return {"comment": comment}


@ic_view_config(
    route_name="comment_vote",
    request_method="PUT",
    permission="vote",
    renderer="comment_contents.jinja2",
)
def put_vote_comment(request: Request) -> dict:
    """Vote on a comment with Intercooler."""
    comment = request.context

    savepoint = request.tm.savepoint()

    new_vote = CommentVote(request.user, comment)
    request.db_session.add(new_vote)

    _mark_comment_read_from_interaction(request, comment)

    request.db_session.add(LogComment(LogEventType.COMMENT_VOTE, request, comment))

    try:
        # manually flush before attempting to commit, to avoid having all objects
        # detached from the session in case of an error
        request.db_session.flush()
        request.tm.commit()
    except IntegrityError:
        # the user has already voted on this comment
        savepoint.rollback()

    # re-query the comment to get complete data
    comment = (
        request.query(Comment)
        .join_all_relationships()
        .filter_by(comment_id=comment.comment_id)
        .one()
    )

    return {"comment": comment}


@ic_view_config(
    route_name="comment_vote",
    request_method="DELETE",
    permission="vote",
    renderer="comment_contents.jinja2",
)
def delete_vote_comment(request: Request) -> dict:
    """Remove the user's vote from a comment with Intercooler."""
    comment = request.context

    request.query(CommentVote).filter(
        CommentVote.comment == comment, CommentVote.user == request.user
    ).delete(synchronize_session=False)

    _mark_comment_read_from_interaction(request, comment)

    request.db_session.add(LogComment(LogEventType.COMMENT_UNVOTE, request, comment))

    # manually commit the transaction so triggers will execute
    request.tm.commit()

    # re-query the comment to get complete data
    comment = (
        request.query(Comment)
        .join_all_relationships()
        .filter_by(comment_id=comment.comment_id)
        .one()
    )

    return {"comment": comment}


@ic_view_config(
    route_name="comment_label",
    request_method="PUT",
    permission="label",
    renderer="comment_contents.jinja2",
)
@use_kwargs(CommentLabelSchema(only=("name",)), locations=("matchdict",))
@use_kwargs(CommentLabelSchema(only=("reason",)))
def put_label_comment(
    request: Request, name: CommentLabelOption, reason: str
) -> Response:
    """Add a label to a comment."""
    comment = request.context

    if not request.user.is_label_available(name):
        raise HTTPUnprocessableEntity("That label is not available.")

    savepoint = request.tm.savepoint()

    weight = request.user.comment_label_weight
    if weight is None:
        weight = request.registry.settings["tildes.default_user_comment_label_weight"]

    label = CommentLabel(comment, request.user, name, weight, reason)
    request.db_session.add(label)

    _mark_comment_read_from_interaction(request, comment)

    try:
        # manually flush before attempting to commit, to avoid having all objects
        # detached from the session in case of an error
        request.db_session.flush()
        request.tm.commit()
    except FlushError:
        savepoint.rollback()

    # re-query the comment to get complete data
    comment = (
        request.query(Comment)
        .join_all_relationships()
        .filter_by(comment_id=comment.comment_id)
        .one()
    )

    return {"comment": comment}


@ic_view_config(
    route_name="comment_label",
    request_method="DELETE",
    permission="label",
    renderer="comment_contents.jinja2",
)
@use_kwargs(CommentLabelSchema(only=("name",)), locations=("matchdict",))
def delete_label_comment(request: Request, name: CommentLabelOption) -> Response:
    """Remove a label (that the user previously added) from a comment."""
    comment = request.context

    request.query(CommentLabel).filter(
        CommentLabel.comment_id == comment.comment_id,
        CommentLabel.user_id == request.user.user_id,
        CommentLabel.label == name,
    ).delete(synchronize_session=False)

    _mark_comment_read_from_interaction(request, comment)

    # commit and then re-query the comment to get complete data
    request.tm.commit()

    comment = (
        request.query(Comment)
        .join_all_relationships()
        .filter_by(comment_id=comment.comment_id)
        .one()
    )

    return {"comment": comment}


@ic_view_config(
    route_name="comment_mark_read", request_method="PUT", permission="mark_read"
)
@use_kwargs({"mark_all_previous": Boolean(missing=False)})
def put_mark_comments_read(request: Request, mark_all_previous: bool) -> Response:
    """Mark comment(s) read, clearing notifications.

    The "main" notification (request.context) will always be marked read, and if the
    query param mark_all_previous is Truthy, all notifications prior to that one will be
    marked read as well.
    """
    notification = request.context

    if mark_all_previous:
        prev_notifications = (
            request.query(CommentNotification)
            .filter(
                CommentNotification.user == request.user,
                CommentNotification.is_unread == True,  # noqa
                CommentNotification.created_time <= notification.created_time,
            )
            .options(joinedload(CommentNotification.comment))
            .all()
        )

        # sort the notifications by created_time of their comment so that the
        # INSERT ... ON CONFLICT DO UPDATE statements work as expected
        prev_notifications = sorted(
            prev_notifications, key=lambda c: c.comment.created_time
        )

        for comment_notification in prev_notifications:
            comment_notification.is_unread = False
            _increment_topic_comments_seen(request, comment_notification.comment)

        return Response("Your comment notifications have been cleared.")

    notification.is_unread = False
    _increment_topic_comments_seen(request, notification.comment)

    return IC_NOOP


@ic_view_config(
    route_name="comment_remove",
    request_method="PUT",
    permission="remove",
    renderer="post_action_toggle_button.jinja2",
)
def put_comment_remove(request: Request) -> dict:
    """Remove a comment with Intercooler."""
    comment = request.context

    comment.is_removed = True
    request.db_session.add(LogComment(LogEventType.COMMENT_REMOVE, request, comment))

    return {"name": "remove", "subject": comment, "is_toggled": True}


@ic_view_config(
    route_name="comment_remove",
    request_method="DELETE",
    permission="remove",
    renderer="post_action_toggle_button.jinja2",
)
def delete_comment_remove(request: Request) -> dict:
    """Un-remove a comment with Intercooler."""
    comment = request.context

    comment.is_removed = False
    request.db_session.add(LogComment(LogEventType.COMMENT_UNREMOVE, request, comment))

    return {"name": "remove", "subject": comment, "is_toggled": False}


@ic_view_config(
    route_name="comment_bookmark",
    request_method="PUT",
    permission="bookmark",
    renderer="post_action_toggle_button.jinja2",
)
def put_comment_bookmark(request: Request) -> dict:
    """Bookmark a comment with Intercooler."""
    comment = request.context

    savepoint = request.tm.savepoint()

    bookmark = CommentBookmark(request.user, comment)
    request.db_session.add(bookmark)

    _mark_comment_read_from_interaction(request, comment)

    try:
        # manually flush before attempting to commit, to avoid having all
        # objects detached from the session in case of an error
        request.db_session.flush()
        request.tm.commit()
    except IntegrityError:
        # the user has already bookmarked this comment
        savepoint.rollback()

    return {"name": "bookmark", "subject": comment, "is_toggled": True}


@ic_view_config(
    route_name="comment_bookmark",
    request_method="DELETE",
    permission="bookmark",
    renderer="post_action_toggle_button.jinja2",
)
def delete_comment_bookmark(request: Request) -> dict:
    """Unbookmark a comment with Intercooler."""
    comment = request.context

    request.query(CommentBookmark).filter(
        CommentBookmark.user == request.user, CommentBookmark.comment == comment
    ).delete(synchronize_session=False)

    _mark_comment_read_from_interaction(request, comment)

    return {"name": "bookmark", "subject": comment, "is_toggled": False}
