# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import timedelta

from freezegun import freeze_time
from pyramid.security import Authenticated, Everyone, principals_allowed_by_permission

from tildes.enums import CommentTreeSortOption
from tildes.lib.datetime import utc_now
from tildes.models.comment import Comment, CommentTree, EDIT_GRACE_PERIOD
from tildes.schemas.comment import CommentSchema
from tildes.schemas.fields import Markdown


def test_comment_creation_validates_schema(mocker, session_user, topic):
    """Ensure that comment creation goes through schema validation."""
    mocker.spy(CommentSchema, "load")

    Comment(topic, session_user, "A test comment")
    call_args = CommentSchema.load.call_args[0]
    assert {"markdown": "A test comment"} in call_args


def test_comment_creation_uses_markdown_field(mocker, session_user, topic):
    """Ensure the Markdown field class is validating new comments."""
    mocker.spy(Markdown, "_validate")

    Comment(topic, session_user, "A test comment")
    assert Markdown._validate.called


def test_comment_edit_uses_markdown_field(mocker, comment):
    """Ensure editing a comment is validated by the Markdown field class."""
    mocker.spy(Markdown, "_validate")

    comment.markdown = "Some new text after edit"
    assert Markdown._validate.called


def test_edit_markdown_updates_html(comment):
    """Ensure editing a comment works and the markdown and HTML update."""
    comment.markdown = "Updated comment"
    assert "Updated" in comment.markdown
    assert "Updated" in comment.rendered_html


def test_comment_viewing_permission(comment):
    """Ensure that anyone can view a comment by default."""
    assert Everyone in principals_allowed_by_permission(comment, "view")


def test_comment_editing_permission(comment):
    """Ensure that only the comment's author can edit it."""
    principals = principals_allowed_by_permission(comment, "edit")
    assert principals == {comment.user_id}


def test_comment_deleting_permission(comment):
    """Ensure that only the comment's author can delete it."""
    principals = principals_allowed_by_permission(comment, "delete")
    assert principals == {comment.user_id}


def test_comment_replying_permission(comment):
    """Ensure that any authenticated user can reply to a comment."""
    assert Authenticated in principals_allowed_by_permission(comment, "reply")


def test_comment_reply_locked_thread_permission(comment):
    """Ensure that only admins can reply in locked threads."""
    comment.topic.is_locked = True
    assert principals_allowed_by_permission(comment, "reply") == {"admin"}


def test_deleted_comment_permissions_removed(comment):
    """Ensure that deleted comments lose all of the permissions."""
    comment.is_deleted = True

    all_permissions = [perm for (_, _, perm) in comment.__acl__()]
    for permission in all_permissions:
        assert not principals_allowed_by_permission(comment, permission)


def test_removed_comment_view_permission(comment):
    """Ensure a removed comment can only be viewed by certain users."""
    comment.is_removed = True
    principals = principals_allowed_by_permission(comment, "view")
    assert principals == {"admin", comment.user_id, "comment.remove"}


def test_edit_grace_period(comment):
    """Ensure last_edited_time isn't set if the edit is inside grace period."""
    one_sec = timedelta(seconds=1)
    edit_time = comment.created_time + EDIT_GRACE_PERIOD - one_sec

    with freeze_time(edit_time):
        comment.markdown = "some new markdown"

    assert not comment.last_edited_time


def test_edit_after_grace_period(comment):
    """Ensure last_edited_time is set after the grace period."""
    one_sec = timedelta(seconds=1)
    edit_time = comment.created_time + EDIT_GRACE_PERIOD + one_sec

    with freeze_time(edit_time):
        comment.markdown = "some new markdown"
        assert comment.last_edited_time == utc_now()


def test_multiple_edits_update_time(comment):
    """Ensure multiple edits all update last_edited_time."""
    one_sec = timedelta(seconds=1)
    initial_time = comment.created_time + EDIT_GRACE_PERIOD + one_sec

    for minutes in range(0, 4):
        edit_time = initial_time + timedelta(minutes=minutes)
        with freeze_time(edit_time):
            comment.markdown = f"edit #{minutes}"
            assert comment.last_edited_time == utc_now()


def test_comment_excerpt_excludes_blockquote(topic, session_user):
    """Ensure that comment excerpts don't include text from blockquotes."""
    markdown = "> Something you said\n\nYeah, I agree."
    comment = Comment(topic, session_user, markdown)

    assert comment.excerpt == "Yeah, I agree."


def test_comment_tree(db, topic, session_user):
    """Ensure that building and pruning a comment tree works."""
    all_comments = []

    sort = CommentTreeSortOption.POSTED

    # add two root comments
    root = Comment(topic, session_user, "root")
    root2 = Comment(topic, session_user, "root2")
    all_comments.extend([root, root2])
    db.add_all(all_comments)
    db.commit()

    # check that both show up in the tree as top-level comments
    tree = CommentTree(all_comments, sort)
    assert list(tree) == [root, root2]

    # delete the second root comment and check that the tree now excludes it
    root2.is_deleted = True
    db.commit()
    tree = list(CommentTree(all_comments, sort))
    assert tree == [root]

    # add two replies to the remaining root comment
    child = Comment(topic, session_user, "1", parent_comment=root)
    child2 = Comment(topic, session_user, "2", parent_comment=root)
    all_comments.extend([child, child2])
    db.add_all(all_comments)
    db.commit()

    # check that the tree is built as expected so far (one root, two replies)
    tree = list(CommentTree(all_comments, sort))
    assert tree == [root]
    assert root.replies == [child, child2]
    assert child.replies == []
    assert child2.replies == []

    # add two more replies to the second depth-1 comment
    subchild = Comment(topic, session_user, "2a", parent_comment=child2)
    subchild2 = Comment(topic, session_user, "2b", parent_comment=child2)
    all_comments.extend([subchild, subchild2])
    db.add_all(all_comments)
    db.commit()

    # check the tree again
    tree = list(CommentTree(all_comments, sort))
    assert tree == [root]
    assert root.replies == [child, child2]
    assert child.replies == []
    assert child2.replies == [subchild, subchild2]

    # delete child2 (which has replies) and ensure it stays in the tree
    child2.is_deleted = True
    db.commit()
    tree = list(CommentTree(all_comments, sort))
    assert root.replies == [child, child2]

    # delete child2's children and ensure that whole branch is pruned
    subchild.is_deleted = True
    subchild2.is_deleted = True
    db.commit()
    tree = list(CommentTree(all_comments, sort))
    assert root.replies == [child]

    # delete root and remaining child and ensure tree is empty
    child.is_deleted = True
    root.is_deleted = True
    db.commit()
    tree = list(CommentTree(all_comments, sort))
    assert not tree
