# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later


def test_tags_whitespace_stripped(text_topic):
    """Ensure excess whitespace around tags gets stripped."""
    text_topic.tags = ["  one", "two   ", "  three "]
    assert text_topic.tags == ["one", "two", "three"]


def test_tag_space_replacement(text_topic):
    """Ensure spaces in tags are converted to underscores internally."""
    text_topic.tags = ["one two", "three four five"]
    assert text_topic._tags == ["one_two", "three_four_five"]


def test_tag_consecutive_spaces(text_topic):
    """Ensure consecutive spaces/underscores in tags are removed."""
    text_topic.tags = ["one  two", "three   four", "five __ six"]
    assert text_topic.tags == ["one two", "three four", "five six"]


def test_duplicate_tags_removed(text_topic):
    """Ensure duplicate tags are removed (case-insensitive)."""
    text_topic.tags = ["one", "one", "One", "ONE", "two", "TWO"]
    assert text_topic.tags == ["one", "two"]


def test_empty_tags_removed(text_topic):
    """Ensure empty tags are removed."""
    text_topic.tags = ["", "  ", "_", "one"]
    assert text_topic.tags == ["one"]


def test_tags_lowercased(text_topic):
    """Ensure tags get converted to lowercase."""
    text_topic.tags = ["ONE", "Two", "thRee"]
    assert text_topic.tags == ["one", "two", "three"]


def test_tags_synonyms(text_topic):
    """ Ensure synonyms are replaced."""
    text_topic.tags = ["spoilers"]
    assert text_topic.tags == ["spoiler"]
