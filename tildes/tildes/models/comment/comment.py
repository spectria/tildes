"""Contains the Comment class."""

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence, Tuple

from pyramid.security import Allow, Authenticated, Deny, DENY_ALL, Everyone
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Text,
    TIMESTAMP,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred, relationship
from sqlalchemy.sql.expression import text

from tildes.lib.datetime import utc_now
from tildes.lib.id import id_to_id36
from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.metrics import incr_counter
from tildes.models import DatabaseModel
from tildes.models.topic import Topic
from tildes.models.user import User
from tildes.schemas.comment import CommentSchema


# edits inside this period after creation will not mark the comment as edited
EDIT_GRACE_PERIOD = timedelta(minutes=2)


class Comment(DatabaseModel):
    """Model for a comment on the site.

    Trigger behavior:
      Incoming:
        - num_votes will be incremented and decremented by insertions and
          deletions in comment_votes.
      Outgoing:
        - Inserting, deleting, or updating is_deleted will increment or
          decrement num_comments on the relevant topic.
        - Inserting a row will increment num_comments on any topic_visit rows
          for the comment's author and the relevant topic.
        - Inserting or updating is_deleted will update last_activity_time on
          the relevant topic.
        - Setting is_deleted to true will delete any rows in
          comment_notifications related to the comment.
        - Setting is_deleted to true will decrement num_comments on all
          topic_visit rows for the relevant topic, where the visit_time was
          after the time the comment was originally posted.
      Internal:
        - deleted_time will be set when is_deleted is set to true
    """

    schema_class = CommentSchema

    __tablename__ = 'comments'

    comment_id: int = Column(Integer, primary_key=True)
    topic_id: int = Column(
        Integer,
        ForeignKey('topics.topic_id'),
        nullable=False,
        index=True,
    )
    user_id: int = Column(
        Integer,
        ForeignKey('users.user_id'),
        nullable=False,
        index=True,
    )
    parent_comment_id: Optional[int] = Column(
        Integer,
        ForeignKey('comments.comment_id'),
        index=True,
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text('NOW()'),
    )
    is_deleted: bool = Column(
        Boolean, nullable=False, server_default='false', index=True)
    deleted_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    is_removed: bool = Column(Boolean, nullable=False, server_default='false')
    removed_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    last_edited_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    _markdown: str = deferred(Column('markdown', Text, nullable=False))
    rendered_html: str = Column(Text, nullable=False)
    num_votes: int = Column(
        Integer, nullable=False, server_default='0', index=True)

    user: User = relationship('User', lazy=False, innerjoin=True)
    topic: Topic = relationship('Topic', innerjoin=True)

    @hybrid_property
    def markdown(self) -> str:
        """Return the comment's markdown."""
        # pylint: disable=method-hidden
        return self._markdown

    @markdown.setter  # type: ignore
    def markdown(self, new_markdown: str) -> None:
        """Set the comment's markdown and render its HTML."""
        if new_markdown == self.markdown:
            return

        self._markdown = new_markdown
        self.rendered_html = convert_markdown_to_safe_html(new_markdown)

        if (self.created_time and
                utc_now() - self.created_time > EDIT_GRACE_PERIOD):
            self.last_edited_time = utc_now()

    def __repr__(self) -> str:
        """Display the comment's ID as its repr format."""
        return f'<Comment ({self.comment_id})>'

    def __init__(
            self,
            topic: Topic,
            author: User,
            markdown: str,
            parent_comment: Optional['Comment'] = None,
    ) -> None:
        """Create a new comment."""
        self.topic = topic
        self.user_id = author.user_id
        if parent_comment:
            self.parent_comment_id = parent_comment.comment_id
        else:
            self.parent_comment_id = None

        self.markdown = markdown

        incr_counter('comments')

    def __acl__(self) -> Sequence[Tuple[str, Any, str]]:
        """Pyramid security ACL."""
        acl = []

        if not (self.is_deleted or self.is_removed):
            acl.append((Allow, Everyone, 'view'))

            if not self.topic.is_locked:
                acl.append((Allow, Authenticated, 'reply'))
            else:
                acl.append((Allow, 'admin', 'reply'))

            acl.append((Allow, Authenticated, 'mark_read'))

            acl.append((Allow, self.user_id, 'edit'))
            acl.append((Allow, self.user_id, 'delete'))

            # everyone except the comment's author can vote on it
            acl.append((Deny, self.user_id, 'vote'))
            acl.append((Allow, Authenticated, 'vote'))

            # temporary - nobody can tag comments
            acl.append((Deny, Everyone, 'tag'))

        if not self.is_deleted:
            acl.append((Allow, 'admin', 'view'))

            acl.append((Allow, self.user_id, 'view'))
            acl.append((Allow, self.user_id, 'reply'))
            acl.append((Allow, self.user_id, 'edit'))
            acl.append((Allow, self.user_id, 'delete'))

        acl.append(DENY_ALL)

        return acl

    @property
    def comment_id36(self) -> str:
        """Return the comment's ID in ID36 format."""
        return id_to_id36(self.comment_id)

    @property
    def parent_comment_id36(self) -> str:
        """Return the parent comment's ID in ID36 format."""
        if not self.parent_comment_id:
            raise AttributeError

        return id_to_id36(self.parent_comment_id)

    @property
    def permalink(self) -> str:
        """Return the permalink for this comment."""
        return f'{self.topic.permalink}#comment-{self.comment_id36}'

    @property
    def parent_comment_permalink(self) -> str:
        """Return the permalink for this comment's parent."""
        if not self.parent_comment_id:
            raise AttributeError

        return f'{self.topic.permalink}#comment-{self.parent_comment_id36}'

    @property
    def tag_counts(self) -> Counter:
        """Counter for number of times each tag is on this comment."""
        return Counter([tag.name for tag in self.tags])

    def tags_by_user(self, user: User) -> Sequence[str]:
        """Return list of tag names that a user has applied to this comment."""
        return [tag.name for tag in self.tags if tag.user_id == user.user_id]
