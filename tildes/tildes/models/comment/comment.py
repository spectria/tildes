# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the Comment class."""

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence, Tuple, TYPE_CHECKING

from pyramid.security import Allow, Authenticated, Deny, DENY_ALL, Everyone
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Text, TIMESTAMP
from sqlalchemy.orm import deferred, relationship
from sqlalchemy.sql.expression import text

from tildes.lib.datetime import utc_now
from tildes.lib.id import id_to_id36
from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.lib.string import extract_text_from_html, truncate_string
from tildes.metrics import incr_counter
from tildes.models import DatabaseModel
from tildes.models.topic import Topic
from tildes.models.user import User
from tildes.schemas.comment import CommentSchema

if TYPE_CHECKING:  # workaround for mypy issues with @hybrid_property
    from builtins import property as hybrid_property
else:
    from sqlalchemy.ext.hybrid import hybrid_property

# edits inside this period after creation will not mark the comment as edited
EDIT_GRACE_PERIOD = timedelta(minutes=5)


class Comment(DatabaseModel):
    """Model for a comment on the site.

    Trigger behavior:
      Incoming:
        - num_votes will be incremented and decremented by insertions and deletions in
          comment_votes.
      Outgoing:
        - Inserting or deleting rows, or updating is_deleted/is_removed to change
          visibility will increment or decrement num_comments accordingly on the
          relevant topic.
        - Inserting a row will increment num_comments on any topic_visit rows for the
          comment's author and the relevant topic.
        - Inserting a new comment or updating is_deleted or is_removed will update
          last_activity_time on the relevant topic.
        - Setting is_deleted or is_removed to true will delete any rows in
          comment_notifications related to the comment.
        - Changing is_deleted or is_removed will adjust num_comments on all topic_visit
          rows for the relevant topic, where the visit_time was after the time the
          comment was originally posted.
        - Inserting a row or updating markdown will send a rabbitmq message for
          "comment.created" or "comment.edited" respectively.
      Internal:
        - deleted_time will be set or unset when is_deleted is changed
    """

    schema_class = CommentSchema

    __tablename__ = "comments"

    comment_id: int = Column(Integer, primary_key=True)
    topic_id: int = Column(
        Integer, ForeignKey("topics.topic_id"), nullable=False, index=True
    )
    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, index=True
    )
    parent_comment_id: Optional[int] = Column(
        Integer, ForeignKey("comments.comment_id"), index=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )
    is_deleted: bool = Column(
        Boolean, nullable=False, server_default="false", index=True
    )
    deleted_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    is_removed: bool = Column(Boolean, nullable=False, server_default="false")
    last_edited_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    _markdown: str = deferred(Column("markdown", Text, nullable=False))
    rendered_html: str = Column(Text, nullable=False)
    excerpt: str = Column(Text, nullable=False, server_default="")
    num_votes: int = Column(Integer, nullable=False, server_default="0", index=True)

    user: User = relationship("User", lazy=False, innerjoin=True)
    topic: Topic = relationship("Topic", innerjoin=True)
    parent_comment: Optional["Comment"] = relationship(
        "Comment", uselist=False, remote_side=[comment_id]
    )

    @hybrid_property
    def markdown(self) -> str:
        """Return the comment's markdown."""
        return self._markdown

    @markdown.setter
    def markdown(self, new_markdown: str) -> None:
        """Set the comment's markdown and render its HTML."""
        if new_markdown == self.markdown:
            return

        self._markdown = new_markdown
        self.rendered_html = convert_markdown_to_safe_html(new_markdown)

        extracted_text = extract_text_from_html(
            self.rendered_html, skip_tags=["blockquote"]
        )
        self.excerpt = truncate_string(
            extracted_text, length=200, truncate_at_chars=" "
        )

        if self.created_time and utc_now() - self.created_time > EDIT_GRACE_PERIOD:
            self.last_edited_time = utc_now()

    def __repr__(self) -> str:
        """Display the comment's ID as its repr format."""
        return f"<Comment ({self.comment_id})>"

    def __init__(
        self,
        topic: Topic,
        author: User,
        markdown: str,
        parent_comment: Optional["Comment"] = None,
    ):
        """Create a new comment."""
        self.topic = topic
        self.user_id = author.user_id
        if parent_comment:
            self.parent_comment_id = parent_comment.comment_id
        else:
            self.parent_comment_id = None

        self.markdown = markdown

        incr_counter("comments")

    def __acl__(self) -> Sequence[Tuple[str, Any, str]]:
        """Pyramid security ACL."""
        acl = []

        # nobody has any permissions on deleted comments
        if self.is_deleted:
            acl.append(DENY_ALL)

        # view:
        #  - removed comments can only be viewed by admins, the author, and users with
        #    remove permission
        #  - otherwise, everyone can view
        if self.is_removed:
            acl.append((Allow, "admin", "view"))
            acl.append((Allow, self.user_id, "view"))
            acl.append((Allow, "comment.remove", "view"))
            acl.append((Deny, Everyone, "view"))

        acl.append((Allow, Everyone, "view"))

        # view exemplary reasons:
        #  - only author gets shown the reasons (admins can see as well with all labels)
        acl.append((Allow, self.user_id, "view_exemplary_reasons"))

        # vote:
        #  - removed comments can't be voted on by anyone
        #  - otherwise, logged-in users except the author can vote
        if self.is_removed:
            acl.append((Deny, Everyone, "vote"))

        acl.append((Deny, self.user_id, "vote"))
        acl.append((Allow, Authenticated, "vote"))

        # label:
        #  - removed comments can't be labeled by anyone
        #  - otherwise, people with the "comment.label" permission other than the author
        if self.is_removed:
            acl.append((Deny, Everyone, "label"))

        acl.append((Deny, self.user_id, "label"))
        acl.append((Allow, "comment.label", "label"))

        # reply:
        #  - removed comments can't be replied to by anyone
        #  - if the topic is locked, only admins can reply
        #  - otherwise, logged-in users can reply
        if self.is_removed:
            acl.append((Deny, Everyone, "reply"))

        if self.topic.is_locked:
            acl.append((Allow, "admin", "reply"))
            acl.append((Deny, Everyone, "reply"))

        acl.append((Allow, Authenticated, "reply"))

        # edit:
        #  - only the author can edit
        acl.append((Allow, self.user_id, "edit"))

        # delete:
        #  - only the author can delete
        acl.append((Allow, self.user_id, "delete"))

        # mark_read:
        #  - logged-in users can mark comments read
        acl.append((Allow, Authenticated, "mark_read"))

        # bookmark:
        #  - logged-in users can bookmark comments
        acl.append((Allow, Authenticated, "bookmark"))

        # tools that require specifically granted permissions
        acl.append((Allow, "admin", "remove"))
        acl.append((Allow, "comment.remove", "remove"))

        acl.append((Allow, "admin", "view_labels"))

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
        return f"{self.topic.permalink}#comment-{self.comment_id36}"

    @property
    def parent_comment_permalink(self) -> str:
        """Return the permalink for this comment's parent."""
        if not self.parent_comment_id:
            raise AttributeError

        return f"{self.topic.permalink}#comment-{self.parent_comment_id36}"

    @property
    def label_counts(self) -> Counter:
        """Counter for number of times each label is on this comment."""
        return Counter([label.name for label in self.labels])

    @property
    def label_weights(self) -> Counter:
        """Counter with cumulative weights of each label on this comment."""
        weights: Counter = Counter()
        for label in self.labels:
            weights[label.name] += label.weight

        return weights

    def labels_by_user(self, user: User) -> Sequence[str]:
        """Return list of label names that a user has applied to this comment."""
        return [label.name for label in self.labels if label.user_id == user.user_id]

    def is_label_active(self, label_name: str) -> bool:
        """Return whether a label has been applied enough to be considered "active"."""
        label_weight = self.label_weights[label_name]

        # Exemplary labels become "active" at 0.5 weight, all others at 1.0
        # Would be best to use the default_user_comment_label_weight value if possible
        if label_name == "exemplary":
            min_weight = 0.5
        else:
            min_weight = 1.0

        if label_weight < min_weight:
            return False

        # for "noise", weight must be more than 1/5 of the vote count (5 votes
        # effectively override 1.0 of label weight)
        if label_name == "noise" and self.num_votes >= label_weight * 5:
            return False

        return True
