# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from pytest import fixture

from tildes.models.comment import Comment
from tildes.models.topic import Topic


@fixture
def text_topic(db, session_group, session_user):
    """Create a text topic, delete it as teardown (including comments)."""
    new_topic = Topic.create_text_topic(
        session_group, session_user, "A Text Topic", "the text"
    )
    db.add(new_topic)
    db.commit()

    yield new_topic

    db.query(Comment).filter_by(topic_id=new_topic.topic_id).delete()
    db.delete(new_topic)
    db.commit()


@fixture
def link_topic(db, session_group, session_user):
    """Create a link topic, delete it as teardown (including comments)."""
    new_topic = Topic.create_link_topic(
        session_group, session_user, "A Link Topic", "http://example.com"
    )
    db.add(new_topic)
    db.commit()

    yield new_topic

    db.query(Comment).filter_by(topic_id=new_topic.topic_id).delete()
    db.delete(new_topic)
    db.commit()


@fixture
def topic(text_topic):
    """Create a topic, test doesn't care which type."""
    return text_topic


@fixture
def comment(db, session_user, topic):
    """Create a comment in the database, delete it as teardown."""
    new_comment = Comment(topic, session_user, "A comment")
    db.add(new_comment)
    db.commit()

    yield new_comment

    db.delete(new_comment)
    db.commit()
