# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Configuration of application routes for URL dispatch."""

from typing import Any

from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.security import Allow, Authenticated

from tildes.resources.comment import comment_by_id36, notification_by_comment_id36
from tildes.resources.group import group_by_path, group_wiki_page_by_slug
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
    with config.route_prefix_context("/~{group_path}"):
        config.add_route("new_topic", "/new_topic", factory=group_by_path)

        config.add_route("group_topics", "/topics", factory=group_by_path)

        config.add_route("group_wiki", "/wiki", factory=group_by_path)

        # if you change this from "new_page" make sure to also edit
        # GroupWikiPage.__init__() to block the new slug to avoid url conflicts
        config.add_route("group_wiki_new_page", "/wiki/new_page", factory=group_by_path)

        config.add_route(
            "group_wiki_page", "/wiki/{wiki_page_slug}", factory=group_wiki_page_by_slug
        )
        config.add_route(
            "group_wiki_edit_page",
            "/wiki/{wiki_page_slug}/edit",
            factory=group_wiki_page_by_slug,
        )

        # these routes need to remain last inside this block
        config.add_route("topic", "/{topic_id36}/{title}", factory=topic_by_id36)
        config.add_route("topic_no_title", "/{topic_id36}", factory=topic_by_id36)

    config.add_route("user", "/user/{username}", factory=user_by_username)
    with config.route_prefix_context("/user/{username}"):
        config.add_route("new_message", "/new_message", factory=user_by_username)
        config.add_route("user_messages", "/messages", factory=user_by_username)

    config.add_route("notifications", "/notifications", factory=LoggedInFactory)
    with config.route_prefix_context("/notifications"):
        config.add_route("notifications_unread", "/unread", factory=LoggedInFactory)

    config.add_route("messages", "/messages", factory=LoggedInFactory)
    with config.route_prefix_context("/messages"):
        config.add_route("messages_sent", "/sent", factory=LoggedInFactory)
        config.add_route("messages_unread", "/unread", factory=LoggedInFactory)
        config.add_route(
            "message_conversation",
            "/conversations/{conversation_id36}",
            factory=message_conversation_by_id36,
        )

    config.add_route("settings", "/settings", factory=LoggedInFactory)
    with config.route_prefix_context("/settings"):
        config.add_route(
            "settings_account_recovery", "/account_recovery", factory=LoggedInFactory
        )
        config.add_route("settings_two_factor", "/two_factor", factory=LoggedInFactory)
        config.add_route(
            "settings_two_factor_qr_code",
            "/two_factor/qr_code",
            factory=LoggedInFactory,
        )
        config.add_route(
            "settings_comment_visits", "/comment_visits", factory=LoggedInFactory
        )
        config.add_route("settings_filters", "/filters", factory=LoggedInFactory)
        config.add_route("settings_bio", "/bio", factory=LoggedInFactory)
        config.add_route(
            "settings_password_change", "/password_change", factory=LoggedInFactory
        )

    config.add_route("bookmarks", "/bookmarks", factory=LoggedInFactory)

    config.add_route("invite", "/invite", factory=LoggedInFactory)

    # Route to expose metrics to Prometheus
    config.add_route("metrics", "/metrics")

    # Route for Stripe donation processing page (POSTed to from docs site)
    config.add_route("donate_stripe", "/donate_stripe")

    # Add all intercooler routes under the /api/web path
    with config.route_prefix_context("/api/web"):
        add_intercooler_routes(config)

    # Add routes for the link-shortener under the /shortener path
    with config.route_prefix_context("/shortener"):
        config.add_route("shortener_group", "/~{group_path}", factory=group_by_path)
        config.add_route("shortener_topic", "/{topic_id36}", factory=topic_by_id36)


def add_intercooler_routes(config: Configurator) -> None:
    """Set up all routes for the (internal-use) Intercooler API endpoints."""

    def add_ic_route(name: str, path: str, **kwargs: Any) -> None:
        """Add route with intercooler name prefix and header check."""
        name = "ic_" + name
        config.add_route(name, path, header="X-IC-Request:true", **kwargs)

    with config.route_prefix_context("/group/{group_path}"):
        add_ic_route("group_subscribe", "/subscribe", factory=group_by_path)
        add_ic_route("group_user_settings", "/user_settings", factory=group_by_path)

    add_ic_route("topic", "/topics/{topic_id36}", factory=topic_by_id36)
    with config.route_prefix_context("/topics/{topic_id36}"):
        add_ic_route("topic_comments", "/comments", factory=topic_by_id36)
        add_ic_route("topic_group", "/group", factory=topic_by_id36)
        add_ic_route("topic_link", "/link", factory=topic_by_id36)
        add_ic_route("topic_lock", "/lock", factory=topic_by_id36)
        add_ic_route("topic_remove", "/remove", factory=topic_by_id36)
        add_ic_route("topic_title", "/title", factory=topic_by_id36)
        add_ic_route("topic_vote", "/vote", factory=topic_by_id36)
        add_ic_route("topic_tags", "/tags", factory=topic_by_id36)
        add_ic_route("topic_bookmark", "/bookmark", factory=topic_by_id36)

    add_ic_route("comment", "/comments/{comment_id36}", factory=comment_by_id36)
    with config.route_prefix_context("/comments/{comment_id36}"):
        add_ic_route("comment_remove", "/remove", factory=comment_by_id36)
        add_ic_route("comment_replies", "/replies", factory=comment_by_id36)
        add_ic_route("comment_vote", "/vote", factory=comment_by_id36)
        add_ic_route("comment_label", "/labels/{name}", factory=comment_by_id36)
        add_ic_route("comment_bookmark", "/bookmark", factory=comment_by_id36)
        add_ic_route(
            "comment_mark_read", "/mark_read", factory=notification_by_comment_id36
        )

    add_ic_route(
        "message_conversation_replies",
        "/messages/conversations/{conversation_id36}/replies",
        factory=message_conversation_by_id36,
    )

    add_ic_route("user", "/user/{username}", factory=user_by_username)
    with config.route_prefix_context("/user/{username}"):
        add_ic_route(
            "user_filtered_topic_tags", "/filtered_topic_tags", factory=user_by_username
        )
        add_ic_route("user_invite_code", "/invite_code", factory=user_by_username)
        add_ic_route(
            "user_default_listing_options",
            "/default_listing_options",
            factory=user_by_username,
        )
        add_ic_route("user_ban", "/ban", factory=user_by_username)

    add_ic_route("markdown_preview", "/markdown_preview", factory=LoggedInFactory)


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
