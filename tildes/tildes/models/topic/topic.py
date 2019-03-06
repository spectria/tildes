# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the Topic class."""

from datetime import datetime, timedelta
from itertools import chain
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, TYPE_CHECKING
from urllib.parse import urlparse

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
from titlecase import titlecase

from tildes.enums import ContentMetadataFields, TopicContentType, TopicType
from tildes.lib.database import TagList
from tildes.lib.datetime import utc_from_timestamp, utc_now
from tildes.lib.id import id_to_id36
from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.lib.site_info import SITE_INFO_BY_DOMAIN
from tildes.lib.string import convert_to_url_slug
from tildes.lib.url import get_domain_from_url
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

# topics can no longer be voted on when they're older than this
VOTING_PERIOD = timedelta(days=30)


class Topic(DatabaseModel):
    """Model for a topic on the site.

    Trigger behavior:
      Incoming:
        - num_votes will be incremented and decremented by insertions and deletions in
          topic_votes (but no decrementing if voting is closed).
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
    schedule_id: int = Column(
        Integer, ForeignKey("topic_schedule.schedule_id"), index=True
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
    content_metadata: Dict[str, Any] = Column(
        MutableDict.as_mutable(JSONB(none_as_null=True))
    )
    num_comments: int = Column(Integer, nullable=False, server_default="0", index=True)
    num_votes: int = Column(Integer, nullable=False, server_default="0", index=True)
    _is_voting_closed: bool = Column(
        "is_voting_closed", Boolean, nullable=False, server_default="false", index=True
    )
    tags: List[str] = Column(TagList, nullable=False, server_default="{}")
    is_official: bool = Column(Boolean, nullable=False, server_default="false")
    is_locked: bool = Column(Boolean, nullable=False, server_default="false")
    search_tsv: Any = deferred(Column(TSVECTOR))

    user: User = relationship("User", lazy=False, innerjoin=True)
    group: Group = relationship("Group", innerjoin=True)

    # Create specialized indexes
    __table_args__ = (
        Index("ix_topics_tags_gist", tags, postgresql_using="gist"),
        Index("ix_topics_search_tsv_gin", "search_tsv", postgresql_using="gin"),
    )

    @hybrid_property  # pylint: disable=used-before-assignment
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

        if self.age > EDIT_GRACE_PERIOD:
            self.last_edited_time = utc_now()

    @property
    def important_tags(self) -> List[str]:
        """Return only the topic's "important" tags."""
        global_important_tags = ["nsfw", "spoiler"]

        important_tags = set(self.group.important_topic_tags + global_important_tags)

        # used with startswith() to check for sub-tags
        important_prefixes = tuple([f"{tag}." for tag in important_tags])

        return [
            tag
            for tag in self.tags
            if tag in important_tags or tag.startswith(important_prefixes)
        ]

    @property
    def unimportant_tags(self) -> List[str]:
        """Return only the topic's tags that *aren't* considered "important"."""
        important_tags = set(self.important_tags)
        return [tag for tag in self.tags if tag not in important_tags]

    @property
    def tags_ordered(self) -> Iterable[str]:
        """Return an iterator over the topic's tags, in a suitable order for display.

        Currently, this puts the "important" tags first, but they're otherwise
        ordered arbitrarily (whatever order they were entered).
        """
        return chain(self.important_tags, self.unimportant_tags)

    def __repr__(self) -> str:
        """Display the topic's title and ID as its repr format."""
        return f'<Topic "{self.title}" ({self.topic_id})>'

    @classmethod
    def _create_base_topic(cls, group: Group, author: User, title: str) -> "Topic":
        """Create the "base" for a new topic."""
        new_topic = cls()
        new_topic.group = group
        new_topic.user = author

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

        return new_topic

    @classmethod
    def create_link_topic(
        cls, group: Group, author: User, title: str, link: str
    ) -> "Topic":
        """Create a new link topic."""
        new_topic = cls._create_base_topic(group, author, title)
        new_topic.topic_type = TopicType.LINK
        new_topic.link = link

        return new_topic

    def _update_creation_metric(self) -> None:
        incr_counter("topics", type=self.topic_type.name.lower())

    def __acl__(self) -> Sequence[Tuple[str, Any, str]]:  # noqa
        """Pyramid security ACL."""
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
        #  - if voting has been closed, nobody can vote
        #  - otherwise, logged-in users except the author can vote
        if self.is_removed:
            acl.append((Deny, Everyone, "vote"))

        if self.is_voting_closed:
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
        #  - only text topics can be edited
        #  - authors can edit their own topics
        #  - admins can edit topics belonging to the generic/automatic user
        if self.is_text_type:
            acl.append((Allow, self.user_id, "edit"))

            if self.user_id == -1:
                acl.append((Allow, "admin", "edit"))

        # delete:
        #  - only the author can delete
        acl.append((Allow, self.user_id, "delete"))

        # tag:
        #  - allow tagging by the author, admins, and people with "topic.tag" principal
        acl.append((Allow, self.user_id, "tag"))
        acl.append((Allow, "admin", "tag"))
        acl.append((Allow, "topic.tag", "tag"))

        # bookmark:
        #  - logged-in users can bookmark topics
        acl.append((Allow, Authenticated, "bookmark"))

        # ignore:
        #  - logged-in users can ignore topics
        acl.append((Allow, Authenticated, "ignore"))

        # edit_title:
        #  - allow admins or people with the "topic.edit_title" permission to always
        #    edit titles
        #  - allow users to edit their own topic's title for the first 5 minutes
        acl.append((Allow, "admin", "edit_title"))
        acl.append((Allow, "topic.edit_title", "edit_title"))

        if self.age < timedelta(minutes=5):
            acl.append((Allow, self.user_id, "edit_title"))

        # tools that require specifically granted permissions
        acl.append((Allow, "admin", "lock"))
        acl.append((Allow, "topic.lock", "lock"))

        acl.append((Allow, "admin", "remove"))
        acl.append((Allow, "topic.remove", "remove"))

        acl.append((Allow, "admin", "move"))
        acl.append((Allow, "topic.move", "move"))

        if self.is_link_type:
            acl.append((Allow, "admin", "edit_link"))
            acl.append((Allow, "topic.edit_link", "edit_link"))

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

        # if there's no SiteInfo object for this domain, just return the domain itself
        try:
            site = SITE_INFO_BY_DOMAIN[self.link_domain]
        except KeyError:
            return self.link_domain

        return site.content_source(self.get_content_metadata("authors"))

    @property
    def is_spoiler(self) -> bool:
        """Return whether the topic is marked as a spoiler."""
        return self.has_tag("spoiler")

    @property
    def is_voting_closed(self) -> bool:
        """Return whether voting on the topic is closed.

        Note that if any logic is changed in here, the close_voting_on_old posts script
        should be updated to match.
        """
        if self._is_voting_closed:
            return True

        if self.age > VOTING_PERIOD:
            return True

        return False

    def has_tag(self, check_tag: str) -> bool:
        """Return whether the topic has a tag or any sub-tag of it."""
        if check_tag in self.tags:
            return True

        if any(tag.startswith(f"{check_tag}.") for tag in self.tags):
            return True

        return False

    @property
    def content_type(self) -> Optional[TopicContentType]:  # noqa
        """Return the content's type based on the topic's attributes."""
        if self.is_text_type:
            if self.has_tag("ask.survey"):
                return TopicContentType.ASK_SURVEY

            if self.has_tag("ask.recommendations"):
                return TopicContentType.ASK_RECOMMENDATIONS

            if self.has_tag("ask.advice"):
                return TopicContentType.ASK_ADVICE

            if self.has_tag("ask"):
                return TopicContentType.ASK

            return TopicContentType.TEXT

        if self.is_link_type:
            parsed_url = urlparse(self.link)
            url_path = PurePosixPath(str(parsed_url.path))

            if url_path.suffix.lower() == ".pdf":
                return TopicContentType.PDF
            elif url_path.suffix.lower() in (".gif", ".jpeg", ".jpg", ".png"):
                return TopicContentType.IMAGE

            # if the site has its own logic in a SiteInfo object, use that
            site = SITE_INFO_BY_DOMAIN.get(self.link_domain)
            if site:
                return site.content_type

            # consider it an article if we picked up a word count of at least 200
            word_count = self.get_content_metadata("word_count")
            if word_count and word_count >= 200:
                return TopicContentType.ARTICLE

        return None

    @property
    def content_type_for_display(self) -> str:
        """Return a string of the topic's content type, suitable for display."""
        if not self.content_type:
            return "Link"

        return self.content_type.display_name

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
        if not self.content_type:
            return ""

        metadata_strings = []

        fields = ContentMetadataFields.detail_fields_for_content_type(self.content_type)

        for field in fields:
            value = self.get_content_metadata(field.key)
            if not value:
                continue

            # only show published date if it's more than 3 days before the topic
            if field is ContentMetadataFields.PUBLISHED:
                published = utc_from_timestamp(value)
                if self.created_time - published < timedelta(days=3):
                    continue

            formatted_value = field.format_value(value)

            if field is ContentMetadataFields.PUBLISHED:
                formatted_value = f"published {formatted_value}"

            metadata_strings.append(formatted_value)

        return ", ".join(metadata_strings)

    @property
    def content_metadata_fields_for_display(self) -> Dict[str, str]:
        """Return a dict of the metadata fields and values, suitable for display."""
        if not self.content_metadata:
            return {}

        output_fields = {}
        for field_name, value in self.content_metadata.items():
            try:
                field = ContentMetadataFields[field_name.upper()]
            except KeyError:
                continue

            output_fields[field.display_name] = field.format_value(value)

        return output_fields

    @property
    def content_excerpt(self) -> Optional[str]:
        """Return the topic's content excerpt (if it has one)."""
        if self.is_text_type:
            return self.get_content_metadata("excerpt")

        if self.content_type is TopicContentType.TWEET:
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

        if self.content_type is TopicContentType.TWEET:
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

    @property
    def was_posted_by_scheduler(self) -> bool:
        """Return whether this topic was posted automatically by the topic scheduler."""
        return bool(self.schedule_id)
