# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the Group class."""

from datetime import datetime
from typing import Any, Optional, Sequence, Tuple

from pyramid.security import Allow, Authenticated, Deny, DENY_ALL, Everyone
from sqlalchemy import Boolean, CheckConstraint, Column, Index, Integer, Text, TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy_utils import Ltree, LtreeType

from tildes.models import DatabaseModel
from tildes.schemas.group import GroupSchema, SHORT_DESCRIPTION_MAX_LENGTH


class Group(DatabaseModel):
    """Model for a group on the site.

    Trigger behavior:
      Incoming:
        - num_subscriptions will be incremented and decremented by insertions and
          deletions in group_subscriptions.
    """

    schema_class = GroupSchema

    __tablename__ = "groups"

    group_id: int = Column(Integer, primary_key=True)
    path: Ltree = Column(LtreeType, nullable=False, index=True, unique=True)
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )
    short_description: Optional[str] = Column(
        Text,
        CheckConstraint(
            f"LENGTH(short_description) <= {SHORT_DESCRIPTION_MAX_LENGTH}",
            name="short_description_length",
        ),
    )
    num_subscriptions: int = Column(Integer, nullable=False, server_default="0")
    is_admin_posting_only: bool = Column(
        Boolean, nullable=False, server_default="false"
    )

    # Create a GiST index on path as well as the btree one that will be created by the
    # index=True/unique=True keyword args to Column above. The GiST index supports
    # additional operators for ltree queries: @>, <@, @, ~, ?
    __table_args__ = (Index("ix_groups_path_gist", path, postgresql_using="gist"),)

    def __repr__(self) -> str:
        """Display the group's path and ID as its repr format."""
        return f"<Group {self.path} ({self.group_id})>"

    def __str__(self) -> str:
        """Use the group path for the string representation."""
        return str(self.path)

    def __lt__(self, other: "Group") -> bool:
        """Order groups by their string representation."""
        return str(self) < str(other)

    def __init__(self, path: str, short_desc: Optional[str] = None):
        """Create a new group."""
        self.path = path
        self.short_description = short_desc

    def __acl__(self) -> Sequence[Tuple[str, Any, str]]:
        """Pyramid security ACL."""
        acl = []

        # view:
        #  - all groups can be viewed by everyone
        acl.append((Allow, Everyone, "view"))

        # subscribe:
        #  - all groups can be subscribed to by logged-in users
        acl.append((Allow, Authenticated, "subscribe"))

        # post_topic:
        #  - only admins can post in admin-posting-only groups
        #  - otherwise, all logged-in users can post
        if self.is_admin_posting_only:
            acl.append((Allow, "admin", "post_topic"))
            acl.append((Deny, Everyone, "post_topic"))

        acl.append((Allow, Authenticated, "post_topic"))

        acl.append(DENY_ALL)

        return acl
