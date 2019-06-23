# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains Enum classes."""

import enum
from typing import Optional


class CommentNotificationType(enum.Enum):
    """Enum for the types of comment notifications."""

    COMMENT_REPLY = enum.auto()
    TOPIC_REPLY = enum.auto()
    USER_MENTION = enum.auto()


class CommentSortOption(enum.Enum):
    """Enum for the different methods out-of-context comments can be sorted by."""

    VOTES = enum.auto()
    NEW = enum.auto()

    @property
    def descending_description(self) -> str:
        """Describe this sort option when used in a "descending" order.

        For example, the "votes" sort has a description of "most votes", since using
        that sort in descending order means that topics with the most votes will be
        listed first.
        """
        if self.name == "NEW":
            return "newest"

        return "most {}".format(self.name.lower())


class CommentTreeSortOption(enum.Enum):
    """Enum for the different methods comment trees can be sorted by."""

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


class CommentLabelOption(enum.Enum):
    """Enum for the (site-wide) comment label options."""

    EXEMPLARY = enum.auto()
    OFFTOPIC = enum.auto()
    JOKE = enum.auto()
    NOISE = enum.auto()
    MALICE = enum.auto()

    @property
    def reason_prompt(self) -> Optional[str]:
        """Return the reason prompt for this label, if any."""
        if self.name == "EXEMPLARY":
            return (
                "Write a short message to say thanks or explain why you appreciated "
                "this comment (required, visible to the comment's author anonymously)"
                "\n\nYou will not be able to use this label again for 8 hours."
            )
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
    COMMENT_UNVOTE = enum.auto()
    COMMENT_VOTE = enum.auto()

    TOPIC_LINK_EDIT = enum.auto()
    TOPIC_LOCK = enum.auto()
    TOPIC_MOVE = enum.auto()
    TOPIC_POST = enum.auto()
    TOPIC_REMOVE = enum.auto()
    TOPIC_TAG = enum.auto()
    TOPIC_TITLE_EDIT = enum.auto()
    TOPIC_UNLOCK = enum.auto()
    TOPIC_UNREMOVE = enum.auto()
    TOPIC_UNVOTE = enum.auto()
    TOPIC_VOTE = enum.auto()


class ScraperType(enum.Enum):
    """Enum for the types of scrapers available."""

    EMBEDLY = enum.auto()
    YOUTUBE = enum.auto()


class TopicSortOption(enum.Enum):
    """Enum for the different methods topics can be sorted by.

    Note that there are two sort methods based on activity:
      - "All activity" will bump a topic back to the top of the sort whenever *any* new
        comments are posted in that topic, similar to how forums behave. This uses the
        Topic.last_activity_time value.
      - "Activity" tries to only bump topics back up when "interesting" activity
        occurs in them, using some checks to decide whether specific comments should be
        disregarded. This uses the topic.last_interesting_activity_time value, which is
        updated by a separate background process (topic_interesting_activity_updater).
    """

    ACTIVITY = enum.auto()
    VOTES = enum.auto()
    COMMENTS = enum.auto()
    NEW = enum.auto()
    ALL_ACTIVITY = enum.auto()

    @property
    def display_name(self) -> str:
        """Return the sort method's name in a format more suitable for display."""
        return self.name.capitalize().replace("_", " ")

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
            return "relevant activity"
        elif self.name == "ALL_ACTIVITY":
            return "all activity"

        return "most {}".format(self.name.lower())


class TopicType(enum.Enum):
    """Enum for the types of topics."""

    TEXT = enum.auto()
    LINK = enum.auto()


class HTMLSanitizationContext(enum.Enum):
    """Enum for the possible contexts for HTML sanitization."""

    USER_BIO = enum.auto()
