"""Contains the Topic class."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

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
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred, relationship
from sqlalchemy.sql.expression import text
from sqlalchemy_utils import Ltree

from tildes.enums import TopicType
from tildes.lib.database import ArrayOfLtree
from tildes.lib.datetime import utc_now
from tildes.lib.id import id_to_id36
from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.lib.string import convert_to_url_slug
from tildes.lib.url import get_domain_from_url
from tildes.metrics import incr_counter
from tildes.models import DatabaseModel
from tildes.models.group import Group
from tildes.models.user import User
from tildes.schemas.topic import (
    TITLE_MAX_LENGTH,
    TopicSchema,
)


# edits inside this period after creation will not mark the topic as edited
EDIT_GRACE_PERIOD = timedelta(minutes=5)

# special tags to put at the front of the tag list
SPECIAL_TAGS = ['nsfw', 'spoiler']


class Topic(DatabaseModel):
    """Model for a topic on the site.

    Trigger behavior:
      Incoming:
        - num_votes will be incremented and decremented by insertions and
          deletions in topic_votes.
        - num_comments will be incremented and decremented by insertions,
          deletions, and updates to is_deleted in comments.
        - last_activity_time will be updated by insertions, deletions, and
          updates to is_deleted in comments.
      Outgoing:
        - Inserting a row or updating markdown will send a rabbitmq message
          for "topic.created" or "topic.edited" respectively.
      Internal:
        - deleted_time will be set when is_deleted is set to true
    """

    schema_class = TopicSchema

    __tablename__ = 'topics'

    topic_id: int = Column(Integer, primary_key=True)
    group_id: int = Column(
        Integer,
        ForeignKey('groups.group_id'),
        nullable=False,
        index=True,
    )
    user_id: int = Column(
        Integer,
        ForeignKey('users.user_id'),
        nullable=False,
        index=True,
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text('NOW()'),
    )
    last_edited_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    last_activity_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text('NOW()'),
    )
    is_deleted: bool = Column(
        Boolean, nullable=False, server_default='false', index=True)
    deleted_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    is_removed: bool = Column(
        Boolean, nullable=False, server_default='false', index=True)
    removed_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    title: str = Column(
        Text,
        CheckConstraint(
            f'LENGTH(title) <= {TITLE_MAX_LENGTH}',
            name='title_length',
        ),
        nullable=False,
    )
    topic_type: TopicType = Column(
        ENUM(TopicType), nullable=False, server_default='TEXT')
    _markdown: Optional[str] = deferred(Column('markdown', Text))
    rendered_html: Optional[str] = Column(Text)
    link: Optional[str] = Column(Text)
    content_metadata: Dict[str, Any] = Column(JSONB)
    num_comments: int = Column(
        Integer, nullable=False, server_default='0', index=True)
    num_votes: int = Column(
        Integer, nullable=False, server_default='0', index=True)
    _tags: List[Ltree] = Column(
        'tags', ArrayOfLtree, nullable=False, server_default='{}')
    is_official: bool = Column(Boolean, nullable=False, server_default='false')
    is_locked: bool = Column(Boolean, nullable=False, server_default='false')

    user: User = relationship('User', lazy=False, innerjoin=True)
    group: Group = relationship('Group', innerjoin=True)

    # Create a GiST index on the tags column
    __table_args__ = (
        Index('ix_topics_tags_gist', _tags, postgresql_using='gist'),
    )

    @hybrid_property
    def markdown(self) -> Optional[str]:
        """Return the topic's markdown."""
        if not self.is_text_type:
            raise AttributeError('Only text topics have markdown')

        return self._markdown

    @markdown.setter  # type: ignore
    def markdown(self, new_markdown: str) -> None:
        """Set the topic's markdown and render its HTML."""
        if not self.is_text_type:
            raise AttributeError('Can only set markdown for text topics')

        if new_markdown == self.markdown:
            return

        self._markdown = new_markdown
        self.rendered_html = convert_markdown_to_safe_html(new_markdown)

        if (self.created_time and
                utc_now() - self.created_time > EDIT_GRACE_PERIOD):
            self.last_edited_time = utc_now()

    @hybrid_property
    def tags(self) -> List[str]:
        """Return the topic's tags."""
        sorted_tags = [str(tag).replace('_', ' ') for tag in self._tags]

        # move special tags in front
        # reverse so that tags at the start of the list appear first
        for tag in reversed(SPECIAL_TAGS):
            if tag in sorted_tags:
                sorted_tags.insert(
                    0, sorted_tags.pop(sorted_tags.index(tag)))

        return sorted_tags

    @tags.setter  # type: ignore
    def tags(self, new_tags: List[str]) -> None:
        self._tags = new_tags

    def __repr__(self) -> str:
        """Display the topic's title and ID as its repr format."""
        return f'<Topic "{self.title}" ({self.topic_id})>'

    @classmethod
    def _create_base_topic(
            cls,
            group: Group,
            author: User,
            title: str,
    ) -> 'Topic':
        """Create the "base" for a new topic."""
        new_topic = cls()
        new_topic.group_id = group.group_id
        new_topic.user_id = author.user_id
        new_topic.title = title

        return new_topic

    @classmethod
    def create_text_topic(
            cls,
            group: Group,
            author: User,
            title: str,
            markdown: str = '',
    ) -> 'Topic':
        """Create a new text topic."""
        new_topic = cls._create_base_topic(group, author, title)
        new_topic.topic_type = TopicType.TEXT
        new_topic.markdown = markdown

        incr_counter('topics', type='text')

        return new_topic

    @classmethod
    def create_link_topic(
            cls,
            group: Group,
            author: User,
            title: str,
            link: str,
    ) -> 'Topic':
        """Create a new link topic."""
        new_topic = cls._create_base_topic(group, author, title)
        new_topic.topic_type = TopicType.LINK
        new_topic.link = link

        incr_counter('topics', type='link')

        return new_topic

    def __acl__(self) -> Sequence[Tuple[str, Any, str]]:
        """Pyramid security ACL."""
        acl = [
            (Allow, Everyone, 'view'),
            (Allow, 'admin', 'lock'),
            (Allow, 'admin', 'move'),
            (Allow, 'admin', 'edit_title'),
            (Allow, 'admin', 'tag'),
        ]

        if not (self.is_locked or self.is_deleted or self.is_removed):
            acl.append((Allow, Authenticated, 'comment'))
        else:
            acl.append((Allow, 'admin', 'comment'))

        if not (self.is_deleted or self.is_removed):
            acl.append((Allow, Everyone, 'view_content'))
            acl.append((Allow, Everyone, 'view_author'))

            # everyone except the topic's author can vote on it
            acl.append((Deny, self.user_id, 'vote'))
            acl.append((Allow, Authenticated, 'vote'))

            acl.append((Allow, self.user_id, 'tag'))

        if not self.is_deleted:
            acl.append((Allow, 'admin', 'view'))

            acl.append((Allow, self.user_id, 'view'))
            acl.append((Allow, self.user_id, 'view_author'))
            acl.append((Allow, self.user_id, 'view_content'))

            if self.is_text_type:
                acl.append((Allow, self.user_id, 'edit'))
            acl.append((Allow, self.user_id, 'delete'))

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
        return f'/~{self.group.path}/{self.topic_id36}/{self.url_slug}'

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
            return 'Text'
        elif self.is_link_type:
            return 'Link'

        return 'Topic'

    @property
    def link_domain(self) -> str:
        """Return the link's domain (for link topics only)."""
        if not self.is_link_type or not self.link:
            raise ValueError('Non-link topics do not have a domain')

        # get the domain from the content metadata if possible, but fall back
        # to just parsing it from the link if it's not present
        return (self.get_content_metadata('domain')
                or get_domain_from_url(self.link))

    def get_content_metadata(self, key: str) -> Any:
        """Get a piece of content metadata "safely".

        Will return None if the topic has no metadata defined, if this key
        doesn't exist in the metadata, etc.
        """
        if not isinstance(self.content_metadata, dict):
            return None

        return self.content_metadata.get(key)

    @property
    def content_metadata_for_display(self) -> str:
        """Return a string of the content's metadata, suitable for display."""
        metadata_strings = []

        if self.is_text_type:
            word_count = self.get_content_metadata('word_count')
            if word_count is not None:
                if word_count == 1:
                    metadata_strings.append('1 word')
                else:
                    metadata_strings.append(f'{word_count} words')
        elif self.is_link_type:
            metadata_strings.append(f'{self.link_domain}')

        return ', '.join(metadata_strings)
