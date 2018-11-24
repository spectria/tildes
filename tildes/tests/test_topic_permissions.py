# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from pyramid.security import Authenticated, Everyone, principals_allowed_by_permission


def test_topic_viewing_permission(text_topic):
    """Ensure that anyone can view a topic by default."""
    principals = principals_allowed_by_permission(text_topic, "view")
    assert Everyone in principals


def test_deleted_topic_permissions_removed(topic):
    """Ensure that deleted topics lose all permissions except "view"."""
    topic.is_deleted = True

    assert principals_allowed_by_permission(topic, "view") == {Everyone}

    all_permissions = [perm for (_, _, perm) in topic.__acl__() if perm != "view"]
    for permission in all_permissions:
        assert not principals_allowed_by_permission(topic, permission)


def test_text_topic_editing_permission(text_topic):
    """Ensure a text topic's owner (and nobody else) is able to edit it."""
    principals = principals_allowed_by_permission(text_topic, "edit")
    assert principals == {text_topic.user.user_id}


def test_link_topic_editing_permission(link_topic):
    """Ensure that nobody has edit permission on a link topic."""
    principals = principals_allowed_by_permission(link_topic, "edit")
    assert not principals


def test_topic_deleting_permission(text_topic):
    """Ensure that the topic's owner (and nobody else) is able to delete it."""
    principals = principals_allowed_by_permission(text_topic, "delete")
    assert principals == {text_topic.user.user_id}


def test_topic_view_author_permission(text_topic):
    """Ensure anyone can view a topic's author normally."""
    principals = principals_allowed_by_permission(text_topic, "view_author")
    assert Everyone in principals


def test_removed_topic_view_author_permission(topic):
    """Ensure only a removed topic's author can only be viewed by certain users."""
    topic.is_removed = True
    principals = principals_allowed_by_permission(topic, "view_author")
    assert principals == {"admin", topic.user_id, "topic.remove"}


def test_topic_view_content_permission(text_topic):
    """Ensure anyone can view a topic's content normally."""
    principals = principals_allowed_by_permission(text_topic, "view_content")
    assert Everyone in principals


def test_removed_topic_view_content_permission(topic):
    """Ensure a removed topic's content can only be viewed by certain users."""
    topic.is_removed = True
    principals = principals_allowed_by_permission(topic, "view_content")
    assert principals == {"admin", topic.user_id, "topic.remove"}


def test_topic_comment_permission(text_topic):
    """Ensure authed users have comment perms on a topic by default."""
    principals = principals_allowed_by_permission(text_topic, "comment")
    assert Authenticated in principals


def test_locked_topic_comment_permission(topic):
    """Ensure only admins can post (top-level) comments on locked topics."""
    topic.is_locked = True
    assert principals_allowed_by_permission(topic, "comment") == {"admin"}


def test_removed_topic_comment_permission(topic):
    """Ensure only admins can post (top-level) comments on removed topics."""
    topic.is_removed = True
    assert principals_allowed_by_permission(topic, "comment") == {"admin"}
