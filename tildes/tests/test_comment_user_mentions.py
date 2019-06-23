# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from pytest import fixture
from sqlalchemy import and_

from tildes.enums import CommentNotificationType
from tildes.models.comment import Comment, CommentNotification
from tildes.models.topic import Topic
from tildes.models.user import User


@fixture
def user_list(db):
    """Create several users."""
    users = []
    for name in ["foo", "bar", "baz"]:
        user = User(name, "password")
        users.append(user)
        db.add(user)
    db.commit()

    yield users

    for user in users:
        db.delete(user)
    db.commit()


def test_get_mentions_for_comment(db, user_list, comment):
    """Test that notifications are generated and returned."""
    comment.markdown = "@foo @bar. @baz!"
    mentions = CommentNotification.get_mentions_for_comment(db, comment)
    assert len(mentions) == 3
    for index, user in enumerate(user_list):
        assert mentions[index].user == user


def test_mention_filtering_parent_comment(mocker, db, topic, user_list):
    """Test notification filtering for parent comments."""
    parent_comment = Comment(topic, user_list[0], "Comment content.")
    parent_comment.user_id = user_list[0].user_id
    comment = mocker.Mock(
        user_id=user_list[1].user_id,
        markdown=f"@{user_list[0].username}",
        parent_comment=parent_comment,
    )
    mentions = CommentNotification.get_mentions_for_comment(db, comment)
    assert not mentions


def test_mention_filtering_self_mention(db, user_list, topic):
    """Test notification filtering for self-mentions."""
    comment = Comment(topic, user_list[0], f"@{user_list[0]}")
    mentions = CommentNotification.get_mentions_for_comment(db, comment)
    assert not mentions


def test_mention_filtering_top_level(db, user_list, session_group):
    """Test notification filtering for top-level comments."""
    topic = Topic.create_text_topic(
        session_group, user_list[0], "Some title", "some text"
    )
    comment = Comment(topic, user_list[1], f"@{user_list[0].username}")
    mentions = CommentNotification.get_mentions_for_comment(db, comment)
    assert not mentions


def test_prevent_duplicate_notifications(db, user_list, topic):
    """Test that notifications are cleaned up for edits.

    Flow:
        1. A comment is created by user A that mentions user B. Notifications are
           generated, and yield A mentioning B.
        2. The comment is edited to mention C and not B.
        3. The comment is edited to mention B and C.
        4. The comment is deleted.
    """
    # 1
    comment = Comment(topic, user_list[0], f"@{user_list[1].username}")
    db.add(comment)
    db.commit()
    mentions = CommentNotification.get_mentions_for_comment(db, comment)
    assert len(mentions) == 1
    assert mentions[0].user == user_list[1]
    db.add_all(mentions)
    db.commit()

    # 2
    comment.markdown = f"@{user_list[2].username}"
    db.commit()
    mentions = CommentNotification.get_mentions_for_comment(db, comment)
    assert len(mentions) == 1
    to_delete, to_add = CommentNotification.prevent_duplicate_notifications(
        db, comment, mentions
    )
    assert len(to_delete) == 1
    assert mentions == to_add
    assert to_delete[0].user.username == user_list[1].username

    # 3
    comment.markdown = f"@{user_list[1].username} @{user_list[2].username}"
    db.commit()
    mentions = CommentNotification.get_mentions_for_comment(db, comment)
    assert len(mentions) == 2
    to_delete, to_add = CommentNotification.prevent_duplicate_notifications(
        db, comment, mentions
    )
    assert not to_delete
    assert len(to_add) == 1

    # 4
    comment.is_deleted = True
    db.commit()
    notifications = (
        db.query(CommentNotification.user_id)
        .filter(
            and_(
                CommentNotification.comment_id == comment.comment_id,
                CommentNotification.notification_type
                == CommentNotificationType.USER_MENTION,
            )
        )
        .all()
    )
    assert not notifications
