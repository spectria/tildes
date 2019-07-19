# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the User class."""

from datetime import datetime, timedelta
from typing import Any, List, Optional, Sequence, Tuple

from mypy_extensions import NoReturn
from pyotp import TOTP
from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Authenticated,
    Deny,
    DENY_ALL,
    Everyone,
)
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    REAL,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred
from sqlalchemy.sql.expression import text
from sqlalchemy_utils import Ltree

from tildes.enums import CommentLabelOption, HTMLSanitizationContext, TopicSortOption
from tildes.lib.database import ArrayOfLtree, CIText
from tildes.lib.datetime import utc_now
from tildes.lib.hash import hash_string, is_match_for_hash
from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.models import DatabaseModel
from tildes.schemas.user import (
    BIO_MAX_LENGTH,
    EMAIL_ADDRESS_NOTE_MAX_LENGTH,
    UserSchema,
)


class User(DatabaseModel):
    """Model for a user's account on the site.

    Trigger behavior:
      Incoming:
        - num_unread_notifications will be incremented and decremented by insertions,
          deletions, and updates to is_unread in comment_notifications.
        - num_unread_messages will be incremented and decremented by insertions,
          deletions, and updates to unread_user_ids in message_conversations.
        - last_exemplary_label_time will be set when a row for an exemplary label is
          inserted into comment_labels.
      Internal:
        - deleted_time will be set when is_deleted is set to true
        - banned_time will be set when is_banned is set to true
    """

    schema_class = UserSchema

    __tablename__ = "users"

    user_id: int = Column(Integer, primary_key=True)
    username: str = Column(CIText, nullable=False, unique=True)
    password_hash: str = deferred(Column(Text, nullable=False))
    email_address_hash: Optional[str] = deferred(Column(Text))
    email_address_note: Optional[str] = deferred(
        Column(
            Text,
            CheckConstraint(
                f"LENGTH(email_address_note) <= {EMAIL_ADDRESS_NOTE_MAX_LENGTH}",
                name="email_address_note_length",
            ),
        )
    )
    two_factor_enabled: bool = Column(Boolean, nullable=False, server_default="false")
    two_factor_secret: Optional[str] = deferred(Column(Text))
    two_factor_backup_codes: List[str] = deferred(Column(ARRAY(Text)))
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )
    num_unread_messages: int = Column(Integer, nullable=False, server_default="0")
    num_unread_notifications: int = Column(Integer, nullable=False, server_default="0")
    inviter_id: int = Column(Integer, ForeignKey("users.user_id"))
    invite_codes_remaining: int = Column(Integer, nullable=False, server_default="0")
    track_comment_visits: bool = Column(Boolean, nullable=False, server_default="false")
    collapse_old_comments: bool = Column(Boolean, nullable=False, server_default="true")
    auto_mark_notifications_read: bool = Column(
        Boolean, nullable=False, server_default="false"
    )
    interact_mark_notifications_read: bool = Column(
        Boolean, nullable=False, server_default="true"
    )
    open_new_tab_external: bool = Column(
        Boolean, nullable=False, server_default="false"
    )
    open_new_tab_internal: bool = Column(
        Boolean, nullable=False, server_default="false"
    )
    open_new_tab_text: bool = Column(Boolean, nullable=False, server_default="false")
    theme_default: str = Column(Text)
    is_deleted: bool = Column(
        Boolean, nullable=False, server_default="false", index=True
    )
    deleted_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    is_banned: bool = Column(Boolean, nullable=False, server_default="false")
    banned_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    permissions: Any = Column(JSONB(none_as_null=True))
    home_default_order: Optional[TopicSortOption] = Column(ENUM(TopicSortOption))
    home_default_period: Optional[str] = Column(Text)
    _filtered_topic_tags: List[Ltree] = Column(
        "filtered_topic_tags", ArrayOfLtree, nullable=False, server_default="{}"
    )
    comment_label_weight: Optional[float] = Column(REAL)
    last_exemplary_label_time: Optional[datetime] = Column(TIMESTAMP(timezone=True))
    _bio_markdown: str = deferred(
        Column(
            "bio_markdown",
            Text,
            CheckConstraint(
                f"LENGTH(bio_markdown) <= {BIO_MAX_LENGTH}", name="bio_markdown_length"
            ),
        )
    )
    bio_rendered_html: str = deferred(Column(Text))

    @hybrid_property
    def filtered_topic_tags(self) -> List[str]:
        """Return the user's list of filtered topic tags."""
        return [str(tag).replace("_", " ") for tag in self._filtered_topic_tags]

    @filtered_topic_tags.setter  # type: ignore
    def filtered_topic_tags(self, new_tags: List[str]) -> None:
        self._filtered_topic_tags = new_tags

    @hybrid_property
    def bio_markdown(self) -> str:
        """Return the user bio's markdown."""
        return self._bio_markdown

    @bio_markdown.setter  # type: ignore
    def bio_markdown(self, new_markdown: str) -> None:
        """Set the user bio's markdown and render its HTML."""
        if new_markdown == self.bio_markdown:
            return

        self._bio_markdown = new_markdown

        if self._bio_markdown is not None:
            self.bio_rendered_html = convert_markdown_to_safe_html(
                new_markdown, HTMLSanitizationContext.USER_BIO
            )
        else:
            self.bio_rendered_html = None

    def __repr__(self) -> str:
        """Display the user's username and ID as its repr format."""
        return f"<User {self.username} ({self.user_id})>"

    def __str__(self) -> str:
        """Use the username for the string representation."""
        return self.username

    def __init__(self, username: str, password: str):
        """Create a new user account."""
        self.username = username
        self.password = password  # type: ignore

    def __acl__(self) -> Sequence[Tuple[str, Any, str]]:
        """Pyramid security ACL."""
        acl = []

        # view:
        #  - everyone can view all users
        acl.append((Allow, Everyone, "view"))

        # view_history:
        #  - only allow logged-in users to look through user history
        acl.append((Allow, Authenticated, "view_history"))

        # view_info:
        #  - can't view info (registration date, bio, etc.) for deleted/banned users
        #  - otherwise, everyone can view
        if self.is_banned or self.is_deleted:
            acl.append((Deny, Everyone, "view_info"))

        acl.append((Allow, Everyone, "view_info"))

        # message:
        #  - deleted and banned users can't be messaged
        #  - otherwise, logged-in users can message anyone except themselves
        if self.is_banned or self.is_deleted:
            acl.append((Deny, Everyone, "message"))

        acl.append((Deny, self.user_id, "message"))
        acl.append((Allow, Authenticated, "message"))

        # ban:
        #  - admins can ban non-deleted users except themselves
        if self.is_deleted:
            acl.append((Deny, Everyone, "ban"))

        acl.append((Deny, self.user_id, "ban"))  # required so users can't self-ban
        acl.append((Allow, "admin", "ban"))

        # grant the user all other permissions on themself
        acl.append((Allow, self.user_id, ALL_PERMISSIONS))

        acl.append(DENY_ALL)

        return acl

    @property
    def password(self) -> NoReturn:
        """Return an error since reading the password isn't possible."""
        raise AttributeError("Password is write-only")

    @password.setter
    def password(self, value: str) -> None:
        # need to do manual validation since some password checks depend on checking the
        # username at the same time (for similarity)
        self.schema.validate({"username": self.username, "password": value})

        self.password_hash = hash_string(value)

    def is_correct_password(self, password: str) -> bool:
        """Check if the password is correct for this user."""
        return is_match_for_hash(password, self.password_hash)

    def change_password(self, old_password: str, new_password: str) -> None:
        """Change the user's password from the old one to a new one."""
        if not self.is_correct_password(old_password):
            raise ValueError("Old password was not correct")

        if new_password == old_password:
            raise ValueError("New password is the same as old password")

        # disable mypy on this line because it doesn't handle setters correctly
        self.password = new_password  # type: ignore

    def is_correct_two_factor_code(self, code: str) -> bool:
        """Verify that a TOTP/backup code is correct."""
        totp = TOTP(self.two_factor_secret)

        code = code.strip().replace(" ", "").lower()

        # some possible user input (such as unicode) can cause an error in the totp
        # library, catch that and treat it the same as an invalid code
        try:
            is_valid_code = totp.verify(code)
        except TypeError:
            is_valid_code = False

        if is_valid_code:
            return True
        elif self.two_factor_backup_codes and code in self.two_factor_backup_codes:
            # Need to set the attribute so SQLAlchemy knows it changed
            self.two_factor_backup_codes = [
                backup_code
                for backup_code in self.two_factor_backup_codes
                if backup_code != code
            ]
            return True

        return False

    @property
    def email_address(self) -> NoReturn:
        """Return an error since reading the email address isn't possible."""
        raise AttributeError("Email address is write-only")

    @email_address.setter
    def email_address(self, value: Optional[str]) -> None:
        """Set the user's email address (will be stored hashed)."""
        if not value:
            self.email_address_hash = None
            return

        # convert the address to lowercase to avoid potential casing issues
        value = value.lower()
        self.email_address_hash = hash_string(value)

    @property
    def num_unread_total(self) -> int:
        """Return total number of unread items (notifications + messages)."""
        return self.num_unread_messages + self.num_unread_notifications

    @property
    def auth_principals(self) -> List[str]:
        """Return the user's authorization principals (used for permissions)."""
        principals: List[str] = []

        # start with any principals manually defined in the permissions column
        if not self.permissions:
            pass
        elif isinstance(self.permissions, str):
            principals = [self.permissions]
        elif isinstance(self.permissions, list):
            principals = self.permissions
        else:
            raise ValueError("Unknown permissions format")

        # give the user the "comment.label" permission if they're over a week old
        if utc_now() - self.created_time > timedelta(days=7):
            principals.append("comment.label")

        return principals

    @property
    def is_admin(self) -> bool:
        """Return whether the user has admin permissions."""
        return "admin" in self.auth_principals

    def is_label_available(self, label: CommentLabelOption) -> bool:
        """Return whether the user has a particular label available."""
        if label == CommentLabelOption.EXEMPLARY:
            if not self.last_exemplary_label_time:
                return True

            return utc_now() - self.last_exemplary_label_time > timedelta(hours=8)

        return True
