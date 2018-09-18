# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains Enum classes."""

from typing import Optional

import enum


class CommentNotificationType(enum.Enum):
    """Enum for the types of comment notifications."""

    COMMENT_REPLY = enum.auto()
    TOPIC_REPLY = enum.auto()
    USER_MENTION = enum.auto()


class CommentSortOption(enum.Enum):
    """Enum for the different methods comments can be sorted by."""

    VOTES = enum.auto()
    NEWEST = enum.auto()
    POSTED = enum.auto()
    RELEVANCE = enum.auto()

    @property
    def description(self) -> str:
        """Describe this sort option."""
        if self.name == "NEWEST":
            return "newest first"
        elif self.name == "POSTED":
            return "order posted"
        elif self.name == "RELEVANCE":
            return "relevance"

        return "most {}".format(self.name.lower())


class CommentTagOption(enum.Enum):
    """Enum for the (site-wide) comment tag options."""

    JOKE = enum.auto()
    OFFTOPIC = enum.auto()
    NOISE = enum.auto()
    MALICE = enum.auto()

    @property
    def reason_prompt(self) -> Optional[str]:
        """Return the reason prompt for this tag, if any."""
        if self.name == "MALICE":
            return "Why is this malicious? (required, will only be visible to admins)"

        return None


class LogEventType(enum.Enum):
    """Enum for the types of events stored in logs."""

    USER_EMAIL_SET = enum.auto()
    USER_LOG_IN = enum.auto()
    USER_LOG_IN_FAIL = enum.auto()
    USER_LOG_OUT = enum.auto()
    USER_REGISTER = enum.auto()

    COMMENT_POST = enum.auto()
    COMMENT_REMOVE = enum.auto()
    COMMENT_UNREMOVE = enum.auto()

    TOPIC_LOCK = enum.auto()
    TOPIC_MOVE = enum.auto()
    TOPIC_POST = enum.auto()
    TOPIC_REMOVE = enum.auto()
    TOPIC_TAG = enum.auto()
    TOPIC_TITLE_EDIT = enum.auto()
    TOPIC_UNLOCK = enum.auto()
    TOPIC_UNREMOVE = enum.auto()


class ScraperType(enum.Enum):
    """Enum for the types of scrapers available."""

    EMBEDLY = enum.auto()


class TopicSortOption(enum.Enum):
    """Enum for the different methods topics can be sorted by."""

    VOTES = enum.auto()
    COMMENTS = enum.auto()
    NEW = enum.auto()
    ACTIVITY = enum.auto()

    @property
    def descending_description(self) -> str:
        """Describe this sort option when used in a "descending" order.

        For example, the "votes" sort has a description of "most votes", since using
        that sort in descending order means that topics with the most votes will be
        listed first.
        """
        if self.name == "NEW":
            return "newest"
        elif self.name == "ACTIVITY":
            return "activity"

        return "most {}".format(self.name.lower())


class TopicType(enum.Enum):
    """Enum for the types of topics."""

    TEXT = enum.auto()
    LINK = enum.auto()
