# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import timedelta

from freezegun import freeze_time
from marshmallow.fields import URL
from pytest import raises

from tildes.lib.datetime import utc_now
from tildes.models.topic import EDIT_GRACE_PERIOD, Topic
from tildes.schemas.fields import Markdown, SimpleString
from tildes.schemas.topic import TopicSchema


def test_text_creation_validations(mocker, session_user, session_group):
    """Ensure that text topic creation goes through expected validation."""
    mocker.spy(TopicSchema, "load")
    mocker.spy(Markdown, "_validate")
    mocker.spy(SimpleString, "_validate")

    Topic.create_text_topic(session_group, session_user, "a title", "the text")

    assert TopicSchema.load.called
    assert SimpleString._validate.call_args[0][1] == "a title"
    assert Markdown._validate.call_args[0][1] == "the text"


def test_link_creation_validations(mocker, session_user, session_group):
    """Ensure that link topic creation goes through expected validation."""
    mocker.spy(TopicSchema, "load")
    mocker.spy(SimpleString, "_validate")
    mocker.spy(URL, "_validate")

    Topic.create_link_topic(
        session_group, session_user, "the title", "http://example.com"
    )

    assert TopicSchema.load.called
    assert SimpleString._validate.call_args[0][1] == "the title"
    assert URL._validate.call_args[0][1] == "http://example.com"


def test_text_topic_edit_uses_markdown_field(mocker, text_topic):
    """Ensure editing a text topic is validated by the Markdown field class."""
    mocker.spy(Markdown, "_validate")

    text_topic.markdown = "Some new text after edit"
    assert Markdown._validate.called


def test_text_topic_type(text_topic):
    """Ensure a text topic has the correct type set."""
    assert text_topic.is_text_type
    assert not text_topic.is_link_type


def test_link_topic_type(link_topic):
    """Ensure a link topic has the correct type set."""
    assert link_topic.is_link_type
    assert not link_topic.is_text_type


def test_delete_sets_deleted_time(db, text_topic):
    """Ensure a deleted topic gets its deleted_time set."""
    assert not text_topic.is_deleted
    assert not text_topic.deleted_time

    text_topic.is_deleted = True
    db.commit()
    db.refresh(text_topic)

    assert text_topic.deleted_time


def test_link_domain_errors_on_text_topic(text_topic):
    """Ensure trying to get the domain of a text topic is an error."""
    with raises(ValueError):
        assert text_topic.link_domain == "this shouldn't work"


def test_link_domain_on_link_topic(link_topic):
    """Ensure getting the domain of a link topic works."""
    assert link_topic.link_domain == "example.com"


def test_edit_markdown_errors_on_link_topic(link_topic):
    """Ensure trying to edit the markdown of a link topic is an error."""
    with raises(AttributeError):
        link_topic.markdown = "Some new markdown"


def test_edit_markdown_on_text_topic(text_topic):
    """Ensure editing the markdown of a text topic works and updates html."""
    original_html = text_topic.rendered_html
    text_topic.markdown = "Some new markdown"
    assert text_topic.rendered_html != original_html


def test_edit_grace_period(text_topic):
    """Ensure last_edited_time isn't set if the edit is inside grace period."""
    one_sec = timedelta(seconds=1)
    edit_time = text_topic.created_time + EDIT_GRACE_PERIOD - one_sec

    with freeze_time(edit_time):
        text_topic.markdown = "some new markdown"

    assert not text_topic.last_edited_time


def test_edit_after_grace_period(text_topic):
    """Ensure last_edited_time is set after the grace period."""
    one_sec = timedelta(seconds=1)
    edit_time = text_topic.created_time + EDIT_GRACE_PERIOD + one_sec

    with freeze_time(edit_time):
        text_topic.markdown = "some new markdown"
        assert text_topic.last_edited_time == utc_now()


def test_multiple_edits_update_time(text_topic):
    """Ensure multiple edits all update last_edited_time."""
    one_sec = timedelta(seconds=1)
    initial_time = text_topic.created_time + EDIT_GRACE_PERIOD + one_sec

    for minutes in range(0, 4):
        edit_time = initial_time + timedelta(minutes=minutes)
        with freeze_time(edit_time):
            text_topic.markdown = f"edit #{minutes}"
            assert text_topic.last_edited_time == utc_now()


def test_topic_initial_last_activity_time(text_topic):
    """Ensure last_activity_time is initially the same as created_time."""
    assert text_topic.last_activity_time == text_topic.created_time


def test_convert_all_caps(session_user, session_group):
    """Ensure that all-caps titles are converted to title case."""
    topic = Topic.create_link_topic(
        session_group, session_user, "THE TITLE", "http://example.com"
    )
    assert topic.title == "The Title"


def test_no_convert_partial_caps_title(session_user, session_group):
    """Ensure that partially-caps titles are not converted to title case."""
    topic = Topic.create_link_topic(
        session_group, session_user, "This is a TITLE", "http://example.com"
    )
    assert topic.title == "This is a TITLE"
