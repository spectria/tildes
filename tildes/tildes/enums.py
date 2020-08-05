# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains Enum classes."""

import enum
from datetime import timedelta
from typing import Any, List, Optional

from tildes.lib.datetime import utc_from_timestamp


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


class ContentMetadataFields(enum.Enum):
    """Enum for the fields of content metadata stored and used (for topics)."""

    AUTHORS = enum.auto()
    DESCRIPTION = enum.auto()
    DOMAIN = enum.auto()
    DURATION = enum.auto()
    EXCERPT = enum.auto()
    PUBLISHED = enum.auto()
    TITLE = enum.auto()
    WORD_COUNT = enum.auto()

    @property
    def key(self) -> str:
        """Return the key to store this field under."""
        return self.name.lower()

    @property
    def display_name(self) -> str:
        """Return the field's name in a format more suitable for display."""
        return self.name.replace("_", " ").capitalize()

    @classmethod
    def detail_fields_for_content_type(
        cls, content_type: "TopicContentType",
    ) -> List["ContentMetadataFields"]:
        """Return a list of fields to display for detail about a particular type."""
        if content_type is TopicContentType.ARTICLE:
            return [cls.WORD_COUNT, cls.PUBLISHED]

        if content_type is TopicContentType.TEXT:
            return [cls.WORD_COUNT]

        if content_type is TopicContentType.VIDEO:
            return [cls.DURATION, cls.PUBLISHED]

        return []

    def format_value(self, value: Any) -> str:
        """Format a value stored in this field into a string for display."""
        if self.name == "AUTHORS":
            return ", ".join(value)

        if self.name == "DURATION":
            delta = timedelta(seconds=value)

            # When converted to str, timedelta always includes hours and minutes,
            # so we want to strip off all the excess zeros and/or colons. However,
            # if it's less than a minute we'll need to add one back.
            duration_str = str(delta).lstrip("0:")
            if value < 60:
                duration_str = f"0:{duration_str}"

            return duration_str

        if self.name == "PUBLISHED":
            published = utc_from_timestamp(value)
            return published.strftime("%b %-d %Y")

        if self.name == "WORD_COUNT":
            if value == 1:
                return "1 word"

            if value >= 10_000:
                # dirty way of using non-breaking thin spaces as thousands separators
                word_count = f"{value:,}".replace(",", "\u202F")
            else:
                word_count = str(value)

            return f"{word_count} words"

        return str(value)


class FinancialEntryType(enum.Enum):
    """Enum for entry types in the Financials table."""

    EXPENSE = enum.auto()
    GOAL = enum.auto()
    INCOME = enum.auto()


class GroupStatType(enum.Enum):
    """Enum for types of group statistics."""

    TOPICS_POSTED = enum.auto()
    COMMENTS_POSTED = enum.auto()


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


class TopicContentType(enum.Enum):
    """Enum for the different types of content for topics."""

    ARTICLE = enum.auto()
    ASK = enum.auto()
    ASK_ADVICE = enum.auto()
    ASK_RECOMMENDATIONS = enum.auto()
    ASK_SURVEY = enum.auto()
    IMAGE = enum.auto()
    PDF = enum.auto()
    TEXT = enum.auto()
    TWEET = enum.auto()
    VIDEO = enum.auto()

    @property
    def display_name(self) -> str:
        """Return the content type's name in a format more suitable for display."""

        if self.name == "PDF":
            return self.name

        if self.name.startswith("ASK_"):
            subtype_name = self.name.partition("_")[-1].lower()
            return f"Ask ({subtype_name})"

        return self.name.capitalize()


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


# Enum for the possible user permissions
# (Using functional API for this one because the values aren't valid Python names)
UserPermission = enum.Enum(
    "UserPermission",
    [
        "comment.remove",
        "comment.view_labels",
        "topic.edit_by_generic_user",
        "topic.edit_link",
        "topic.edit_title",
        "topic.lock",
        "topic.move",
        "topic.post",
        "topic.remove",
        "topic.tag",
        "user.ban",
        "user.view_removed_posts",
        "wiki.edit",
    ],
)


class UserPermissionType(enum.Enum):
    """Enum for the types of user permissions."""

    ALLOW = enum.auto()
    DENY = enum.auto()
