# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from tildes.models.comment import Comment


def test_comments_affect_topic_num_comments(session_user, topic, db):
    """Ensure adding/deleting comments affects the topic's comment count."""
    assert topic.num_comments == 0

    # Insert some comments, ensure each one increments the count
    comments = []
    for num in range(0, 5):
        new_comment = Comment(topic, session_user, "comment")
        comments.append(new_comment)
        db.add(new_comment)
        db.commit()
        db.refresh(topic)
        assert topic.num_comments == len(comments)

    # Delete all the comments, ensure each one decrements the count
    for num, comment in enumerate(comments, start=1):
        comment.is_deleted = True
        db.commit()
        db.refresh(topic)
        assert topic.num_comments == len(comments) - num


def test_delete_sets_deleted_time(db, comment):
    """Ensure a deleted comment gets its deleted_time set and unset."""
    assert not comment.is_deleted
    assert not comment.deleted_time

    comment.is_deleted = True
    db.commit()
    db.refresh(comment)

    assert comment.deleted_time

    comment.is_deleted = False
    db.commit()
    db.refresh(comment)

    assert not comment.deleted_time


def test_remove_delete_single_decrement(db, topic, session_user):
    """Ensure that remove+delete doesn't double-decrement num_comments."""
    # add 2 comments
    comment1 = Comment(topic, session_user, "Comment 1")
    comment2 = Comment(topic, session_user, "Comment 2")
    db.add_all([comment1, comment2])
    db.commit()
    db.refresh(topic)
    assert topic.num_comments == 2

    # remove one and check the decrement
    comment1.is_removed = True
    db.add(comment1)
    db.commit()
    db.refresh(topic)
    assert topic.num_comments == 1

    # delete the same comment and check it didn't decrement again
    comment1.is_deleted = True
    db.add(comment1)
    db.commit()
    db.refresh(topic)
    assert topic.num_comments == 1
