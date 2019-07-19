# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the Topic class."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple, TYPE_CHECKING

from pyramid.security import Allow, Authenticated, Deny, DENY_ALL, Everyone
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, TSVECTOR
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import deferred, relationship
from sqlalchemy.sql.expression import text
from sqlalchemy_utils import Ltree
from titlecase import titlecase

from tildes.enums import TopicType
from tildes.lib.database import ArrayOfLtree
from tildes.lib.datetime import utc_from_timestamp, utc_now
from tildes.lib.id import id_to_id36
from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.lib.string import convert_to_url_slug
from tildes.lib.url import get_domain_from_url, is_tweet
from tildes.metrics import incr_counter
from tildes.models import DatabaseModel
from tildes.models.group import Group
from tildes.models.user import User
from tildes.schemas.topic import TITLE_MAX_LENGTH, TopicSchema

if TYPE_CHECKING:  # workaround for mypy issues with @hybrid_property
    from builtins import property as hybrid_property
else:
    from sqlalchemy.ext.hybrid import hybrid_property

# edits inside this period after creation will not mark the topic as edited
EDIT_GRACE_PERIOD = timedelta(minutes=5)

# special tags to put at the front of the tag list
SPECIAL_TAGS = ["nsfw", "spoiler"]


class Topic(DatabaseModel):
    """Model for a topic on the site.

    Trigger behavior:
      Incoming:
        - num_votes will be incremented and decremented by insertions and deletions in
          topic_votes.
        - num_comments will be incremented and decremented by insertions, deletions, and
          updates to is_deleted in comments.
        - last_activity_time will be updated by insertions, deletions, and updates to
          is_deleted in comments.
      Outgoing:
        - Inserting a row will send a rabbitmq "topic.created" message.
        - Updating markdown will send a rabbitmq "topic.edited" message.
        - Updating link will send a rabbitmq "topic.link_edited" message.
      Internal:
        - deleted_time will be set when is_deleted is set to true
    """

    schema_class = TopicSchema

    __tablename__ = "topics"

    topic_id: int = Column(Integer, primary_key=True)
    group_id: int = Column(
        Integer, ForeignKey("groups.group_id"), nullable=False, index=True
    )
    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, index=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )
    last_edited_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    last_activity_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )
    last_interesting_activity_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )
    is_deleted: bool = Column(
        Boolean, nullable=False, server_default="false", index=True
    )
    deleted_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    is_removed: bool = Column(
        Boolean, nullable=False, server_default="false", index=True
    )
    title: str = Column(
        Text,
        CheckConstraint(f"LENGTH(title) <= {TITLE_MAX_LENGTH}", name="title_length"),
        nullable=False,
    )
    topic_type: TopicType = Column(
        ENUM(TopicType), nullable=False, server_default="TEXT"
    )
    _markdown: Optional[str] = deferred(Column("markdown", Text))
    rendered_html: Optional[str] = Column(Text)
    link: Optional[str] = Column(Text)
    original_url: Optional[str] = Column(Text)
    content_metadata: Dict[str, Any] = Column(
        MutableDict.as_mutable(JSONB(none_as_null=True))
    )
    num_comments: int = Column(Integer, nullable=False, server_default="0", index=True)
    num_votes: int = Column(Integer, nullable=False, server_default="0", index=True)
    _tags: List[Ltree] = Column(
        "tags", ArrayOfLtree, nullable=False, server_default="{}"
    )
    is_official: bool = Column(Boolean, nullable=False, server_default="false")
    is_locked: bool = Column(Boolean, nullable=False, server_default="false")
    search_tsv: Any = deferred(Column(TSVECTOR))

    user: User = relationship("User", lazy=False, innerjoin=True)
    group: Group = relationship("Group", innerjoin=True)

    # Create specialized indexes
    __table_args__ = (
        Index("ix_topics_tags_gist", _tags, postgresql_using="gist"),
        Index("ix_topics_search_tsv_gin", "search_tsv", postgresql_using="gin"),
    )

    @hybrid_property
    def markdown(self) -> Optional[str]:
        """Return the topic's markdown."""
        if not self.is_text_type:
            raise AttributeError("Only text topics have markdown")

        return self._markdown

    @markdown.setter
    def markdown(self, new_markdown: str) -> None:
        """Set the topic's markdown and render its HTML."""
        if not self.is_text_type:
            raise AttributeError("Can only set markdown for text topics")

        if new_markdown == self.markdown:
            return

        self._markdown = new_markdown
        self.rendered_html = convert_markdown_to_safe_html(new_markdown)

        if self.created_time and utc_now() - self.created_time > EDIT_GRACE_PERIOD:
            self.last_edited_time = utc_now()

    @hybrid_property
    def tags(self) -> List[str]:
        """Return the topic's tags."""
        sorted_tags = [str(tag).replace("_", " ") for tag in self._tags]

        # move special tags in front
        # reverse so that tags at the start of the list appear first
        for tag in reversed(SPECIAL_TAGS):
            if tag in sorted_tags:
                sorted_tags.insert(0, sorted_tags.pop(sorted_tags.index(tag)))

        return sorted_tags

    @tags.setter
    def tags(self, new_tags: List[str]) -> None:
        self._tags = new_tags

    def __repr__(self) -> str:
        """Display the topic's title and ID as its repr format."""
        return f'<Topic "{self.title}" ({self.topic_id})>'

    @classmethod
    def _create_base_topic(cls, group: Group, author: User, title: str) -> "Topic":
        """Create the "base" for a new topic."""
        new_topic = cls()
        new_topic.group_id = group.group_id
        new_topic.user_id = author.user_id

        # if the title is all caps, convert to title case
        if title.isupper():
            title = titlecase(title)

        new_topic.title = title

        return new_topic

    @classmethod
    def create_text_topic(
        cls, group: Group, author: User, title: str, markdown: str = ""
    ) -> "Topic":
        """Create a new text topic."""
        new_topic = cls._create_base_topic(group, author, title)
        new_topic.topic_type = TopicType.TEXT
        new_topic.markdown = markdown

        incr_counter("topics", type="text")

        return new_topic

    @classmethod
    def create_link_topic(
        cls, group: Group, author: User, title: str, link: str
    ) -> "Topic":
        """Create a new link topic."""
        new_topic = cls._create_base_topic(group, author, title)
        new_topic.topic_type = TopicType.LINK
        new_topic.link = link
        new_topic.original_url = link

        incr_counter("topics", type="link")

        return new_topic

    def __acl__(self) -> Sequence[Tuple[str, Any, str]]:
        """Pyramid security ACL."""
        # pylint: disable=too-many-branches
        acl = []

        # deleted topics allow "general" viewing, but nothing else
        if self.is_deleted:
            acl.append((Allow, Everyone, "view"))
            acl.append(DENY_ALL)

        # view:
        #  - everyone gets "general" viewing permission for all topics
        acl.append((Allow, Everyone, "view"))

        # view_author:
        #  - removed topics' author is only visible to the author, admins, and users
        #    with remove permission
        #  - otherwise, everyone can view the author
        if self.is_removed:
            acl.append((Allow, "admin", "view_author"))
            acl.append((Allow, self.user_id, "view_author"))
            acl.append((Allow, "topic.remove", "view_author"))
            acl.append((Deny, Everyone, "view_author"))

        acl.append((Allow, Everyone, "view_author"))

        # view_content:
        #  - removed topics' content is only visible to the author, admins and users
        #    with remove permissions
        #  - otherwise, everyone can view the content
        if self.is_removed:
            acl.append((Allow, "admin", "view_content"))
            acl.append((Allow, self.user_id, "view_content"))
            acl.append((Allow, "topic.remove", "view_content"))
            acl.append((Deny, Everyone, "view_content"))

        acl.append((Allow, Everyone, "view_content"))

        # vote:
        #  - removed topics can't be voted on by anyone
        #  - otherwise, logged-in users except the author can vote
        if self.is_removed:
            acl.append((Deny, Everyone, "vote"))

        acl.append((Deny, self.user_id, "vote"))
        acl.append((Allow, Authenticated, "vote"))

        # comment:
        #  - removed topics can only be commented on by admins
        #  - locked topics can only be commented on by admins
        #  - otherwise, logged-in users can comment
        if self.is_removed:
            acl.append((Allow, "admin", "comment"))
            acl.append((Deny, Everyone, "comment"))

        if self.is_locked:
            acl.append((Allow, "admin", "comment"))
            acl.append((Deny, Everyone, "comment"))

        acl.append((Allow, Authenticated, "comment"))

        # edit:
        #  - only text topics can be edited, only by the author
        if self.is_text_type:
            acl.append((Allow, self.user_id, "edit"))

        # delete:
        #  - only the author can delete
        acl.append((Allow, self.user_id, "delete"))

        # tag:
        #  - allow tagging by the author, admins, and people with "topic.tag" principal
        acl.append((Allow, self.user_id, "tag"))
        acl.append((Allow, "admin", "tag"))
        acl.append((Allow, "topic.tag", "tag"))

        # tools that require specifically granted permissions
        acl.append((Allow, "admin", "lock"))
        acl.append((Allow, "topic.lock", "lock"))

        acl.append((Allow, "admin", "remove"))
        acl.append((Allow, "topic.remove", "remove"))

        acl.append((Allow, "admin", "move"))
        acl.append((Allow, "topic.move", "move"))

        acl.append((Allow, "admin", "edit_title"))
        acl.append((Allow, "topic.edit_title", "edit_title"))

        if self.is_link_type:
            acl.append((Allow, "admin", "edit_link"))
            acl.append((Allow, "topic.edit_link", "edit_link"))

        # bookmark:
        #  - logged-in users can bookmark topics
        acl.append((Allow, Authenticated, "bookmark"))

        acl.append(DENY_ALL)

        return acl

    @property
    def topic_id36(self) -> str:
        """Return the topic's ID in ID36 format."""
        return id_to_id36(self.topic_id)

    @property
    def url_slug(self) -> str:
        """Return the url slug for this topic."""
        return convert_to_url_slug(self.title)

    @property
    def permalink(self) -> str:
        """Return the permalink for this topic."""
        return f"/~{self.group.path}/{self.topic_id36}/{self.url_slug}"

    @property
    def is_text_type(self) -> bool:
        """Return whether this is a text topic."""
        return self.topic_type is TopicType.TEXT

    @property
    def is_link_type(self) -> bool:
        """Return whether this is a link topic."""
        return self.topic_type is TopicType.LINK

    @property
    def type_for_display(self) -> str:
        """Return a string of the topic's type, suitable for display."""
        if self.is_text_type:
            return "Text"
        elif self.is_link_type:
            return "Link"

        return "Topic"

    @property
    def link_domain(self) -> str:
        """Return the link's domain (for link topics only)."""
        if not self.is_link_type or not self.link:
            raise ValueError("Non-link topics do not have a domain")

        # get the domain from the content metadata if possible, but fall back to just
        # parsing it from the link if it's not present
        return self.get_content_metadata("domain") or get_domain_from_url(self.link)

    @property
    def link_source(self) -> str:
        """Return the link's "source", which can be defined for certain domains.

        If special behavior isn't defined for a domain, this just falls back to
        returning the domain itself.
        """
        if not self.is_link_type:
            raise ValueError("Non-link topics do not have a link source")

        domain = self.link_domain
        authors = self.get_content_metadata("authors")

        if domain == "twitter.com" and authors:
            return f"Twitter: @{authors[0]}"
        elif domain == "youtube.com" and authors:
            return f"YouTube: {authors[0]}"

        return domain

    @property
    def is_spoiler(self) -> bool:
        """Return whether the topic is marked as a spoiler."""
        return "spoiler" in self.tags

    def get_content_metadata(self, key: str) -> Any:
        """Get a piece of content metadata "safely".

        Will return None if the topic has no metadata defined, if this key doesn't exist
        in the metadata, etc.
        """
        if not isinstance(self.content_metadata, dict):
            return None

        return self.content_metadata.get(key)

    @property
    def content_metadata_for_display(self) -> str:
        """Return a string of the content's metadata, suitable for display."""
        # pylint: disable=too-many-branches
        metadata_strings = []

        # display word count (if we have it) with either type of topic
        word_count = self.get_content_metadata("word_count")
        if word_count is not None:
            if word_count == 1:
                metadata_strings.append("1 word")
            else:
                metadata_strings.append(f"{word_count} words")

        if self.is_link_type:
            # display the duration if we have it
            duration = self.get_content_metadata("duration")
            if duration:
                duration_delta = timedelta(seconds=duration)

                # When converted to str, timedelta always includes hours and minutes,
                # so we want to strip off all the excess zeros and/or colons. However,
                # if it's less than a minute we'll need to add one back.
                duration_str = str(duration_delta).lstrip("0:")
                if duration < 60:
                    duration_str = f"0:{duration_str}"

                metadata_strings.append(duration_str)

            # display the published date if it's more than 3 days before the topic
            published_timestamp = self.get_content_metadata("published")
            if published_timestamp:
                published = utc_from_timestamp(published_timestamp)
                if self.created_time - published > timedelta(days=3):
                    metadata_strings.append(published.strftime("%b %-d %Y"))

        return ", ".join(metadata_strings)

    @property
    def content_excerpt(self) -> Optional[str]:
        """Return the topic's content excerpt (if it has one)."""
        if self.is_text_type:
            return self.get_content_metadata("excerpt")

        if self.link and is_tweet(self.link):
            authors = self.get_content_metadata("authors")
            tweet = self.get_content_metadata("description")

            if authors and tweet:
                return f"@{authors[0]}: {tweet}"

        return None

    @property
    def is_content_excerpt_truncated(self) -> bool:
        """Return whether the content excerpt has been truncated or not."""
        if self.is_text_type and self.content_excerpt:
            return self.content_excerpt.endswith("...")

        return False

    @property
    def additional_content_html(self) -> Optional[str]:
        """Additional HTML related to the content that can be displayed."""
        if not self.is_link_type:
            return None

        if self.link and is_tweet(self.link):
            authors = self.get_content_metadata("authors")
            tweet = self.get_content_metadata("description")

            if authors and tweet:
                return f"<cite>@{authors[0]}:</cite><blockquote>{tweet}</blockquote>"

        return None

    @property
    def is_user_treated_as_source(self) -> bool:
        """Return whether the user that posted the topic is its "source"."""
        if self.group.is_user_treated_as_topic_source:
            return True

        return self.is_text_type
