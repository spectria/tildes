# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Configuration of application routes for URL dispatch."""

from typing import Any

from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.security import Allow, Authenticated

from tildes.resources.comment import comment_by_id36, notification_by_comment_id36
from tildes.resources.group import group_by_path
from tildes.resources.message import message_conversation_by_id36
from tildes.resources.topic import topic_by_id36
from tildes.resources.user import user_by_username


def includeme(config: Configurator) -> None:
    """Set up application routes."""
    config.add_route("home", "/")

    config.add_route("search", "/search")

    config.add_route("groups", "/groups")

    config.add_route("login", "/login")
    config.add_route("login_two_factor", "/login_two_factor")
    config.add_route("logout", "/logout", factory=LoggedInFactory)

    config.add_route("register", "/register")

    config.add_route("group", "/~{group_path}", factory=group_by_path)
    config.add_route("new_topic", "/~{group_path}/new_topic", factory=group_by_path)

    config.add_route("group_topics", "/~{group_path}/topics", factory=group_by_path)

    config.add_route(
        "topic", "/~{group_path}/{topic_id36}*title", factory=topic_by_id36
    )

    config.add_route("user", "/user/{username}", factory=user_by_username)

    config.add_route("notifications", "/notifications", factory=LoggedInFactory)
    config.add_route(
        "notifications_unread", "/notifications/unread", factory=LoggedInFactory
    )

    config.add_route("messages", "/messages", factory=LoggedInFactory)
    config.add_route("messages_sent", "/messages/sent", factory=LoggedInFactory)
    config.add_route("messages_unread", "/messages/unread", factory=LoggedInFactory)
    config.add_route(
        "message_conversation",
        "/messages/conversations/{conversation_id36}",
        factory=message_conversation_by_id36,
    )
    config.add_route(
        "new_message", "/user/{username}/new_message", factory=user_by_username
    )
    config.add_route(
        "user_messages", "/user/{username}/messages", factory=user_by_username
    )

    config.add_route("settings", "/settings", factory=LoggedInFactory)
    config.add_route(
        "settings_account_recovery",
        "/settings/account_recovery",
        factory=LoggedInFactory,
    )
    config.add_route(
        "settings_two_factor", "/settings/two_factor", factory=LoggedInFactory
    )
    config.add_route(
        "settings_two_factor_qr_code",
        "/settings/two_factor/qr_code",
        factory=LoggedInFactory,
    )
    config.add_route(
        "settings_comment_visits", "/settings/comment_visits", factory=LoggedInFactory
    )
    config.add_route("settings_filters", "/settings/filters", factory=LoggedInFactory)
    config.add_route(
        "settings_password_change", "/settings/password_change", factory=LoggedInFactory
    )

    config.add_route("bookmarks", "/bookmarks", factory=LoggedInFactory)

    config.add_route("invite", "/invite", factory=LoggedInFactory)

    # Route to expose metrics to Prometheus
    config.add_route("metrics", "/metrics")

    # Route for Stripe donation processing page (POSTed to from docs site)
    config.add_route("donate_stripe", "/donate_stripe")

    add_intercooler_routes(config)


def add_intercooler_routes(config: Configurator) -> None:
    """Set up all routes for the (internal-use) Intercooler API endpoints."""

    def add_ic_route(name: str, path: str, **kwargs: Any) -> None:
        """Add route with intercooler name prefix, base path, header check."""
        name = "ic_" + name
        path = "/api/web" + path
        config.add_route(name, path, header="X-IC-Request:true", **kwargs)

    add_ic_route(
        "group_subscribe", "/group/{group_path}/subscribe", factory=group_by_path
    )
    add_ic_route(
        "group_user_settings",
        "/group/{group_path}/user_settings",
        factory=group_by_path,
    )

    add_ic_route("topic", "/topics/{topic_id36}", factory=topic_by_id36)
    add_ic_route(
        "topic_comments", "/topics/{topic_id36}/comments", factory=topic_by_id36
    )
    add_ic_route("topic_group", "/topics/{topic_id36}/group", factory=topic_by_id36)
    add_ic_route("topic_lock", "/topics/{topic_id36}/lock", factory=topic_by_id36)
    add_ic_route("topic_remove", "/topics/{topic_id36}/remove", factory=topic_by_id36)
    add_ic_route("topic_title", "/topics/{topic_id36}/title", factory=topic_by_id36)
    add_ic_route("topic_vote", "/topics/{topic_id36}/vote", factory=topic_by_id36)
    add_ic_route("topic_tags", "/topics/{topic_id36}/tags", factory=topic_by_id36)
    add_ic_route(
        "topic_bookmark", "/topics/{topic_id36}/bookmark", factory=topic_by_id36
    )

    add_ic_route("comment", "/comments/{comment_id36}", factory=comment_by_id36)
    add_ic_route(
        "comment_remove", "/comments/{comment_id36}/remove", factory=comment_by_id36
    )
    add_ic_route(
        "comment_replies", "/comments/{comment_id36}/replies", factory=comment_by_id36
    )
    add_ic_route(
        "comment_vote", "/comments/{comment_id36}/vote", factory=comment_by_id36
    )
    add_ic_route(
        "comment_label",
        "/comments/{comment_id36}/labels/{name}",
        factory=comment_by_id36,
    )
    add_ic_route(
        "comment_bookmark", "/comments/{comment_id36}/bookmark", factory=comment_by_id36
    )
    add_ic_route(
        "comment_mark_read",
        "/comments/{comment_id36}/mark_read",
        factory=notification_by_comment_id36,
    )

    add_ic_route(
        "message_conversation_replies",
        "/messages/conversations/{conversation_id36}/replies",
        factory=message_conversation_by_id36,
    )

    add_ic_route("user", "/user/{username}", factory=user_by_username)
    add_ic_route(
        "user_filtered_topic_tags",
        "/user/{username}/filtered_topic_tags",
        factory=user_by_username,
    )
    add_ic_route(
        "user_invite_code", "/user/{username}/invite_code", factory=user_by_username
    )
    add_ic_route(
        "user_default_listing_options",
        "/user/{username}/default_listing_options",
        factory=user_by_username,
    )


class LoggedInFactory:
    """Simple class to use as `factory` to restrict routes to logged-in users.

    This class can be used when a route should only be accessible to logged-in users but
    doesn't already have another factory that would handle that by checking access to a
    specific resource (such as a topic or message).
    """

    __acl__ = ((Allow, Authenticated, "view"),)

    def __init__(self, request: Request):
        """Initialize - no-op, but needs to take the request as an arg."""
        pass
