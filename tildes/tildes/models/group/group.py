# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the Group class."""

from datetime import datetime
from typing import Any, List, Optional, Sequence, Tuple

from pyramid.security import Allow, Authenticated, Deny, DENY_ALL, Everyone
from sqlalchemy import Boolean, CheckConstraint, Column, Index, Integer, Text, TIMESTAMP
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred
from sqlalchemy.sql.expression import text
from sqlalchemy_utils import Ltree, LtreeType

from tildes.lib.database import ArrayOfLtree
from tildes.lib.markdown import convert_markdown_to_safe_html
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
    _sidebar_markdown: str = deferred(Column("sidebar_markdown", Text))
    sidebar_rendered_html: str = deferred(Column(Text))
    num_subscriptions: int = Column(Integer, nullable=False, server_default="0")
    is_admin_posting_only: bool = Column(
        Boolean, nullable=False, server_default="false"
    )
    is_user_treated_as_topic_source: bool = Column(
        Boolean, nullable=False, server_default="false"
    )
    _common_topic_tags: List[Ltree] = Column(
        "common_topic_tags", ArrayOfLtree, nullable=False, server_default="{}"
    )

    # Create a GiST index on path as well as the btree one that will be created by the
    # index=True/unique=True keyword args to Column above. The GiST index supports
    # additional operators for ltree queries: @>, <@, @, ~, ?
    __table_args__ = (Index("ix_groups_path_gist", path, postgresql_using="gist"),)

    @hybrid_property
    def common_topic_tags(self) -> List[str]:
        """Return the group's list of common topic tags."""
        return [str(tag).replace("_", " ") for tag in self._common_topic_tags]

    @common_topic_tags.setter  # type: ignore
    def common_topic_tags(self, new_tags: List[str]) -> None:
        self._common_topic_tags = new_tags

    @hybrid_property
    def sidebar_markdown(self) -> str:
        """Return the sidebar's markdown."""
        return self._sidebar_markdown

    @sidebar_markdown.setter  # type: ignore
    def sidebar_markdown(self, new_markdown: str) -> None:
        """Set the sidebar's markdown and render its HTML."""
        if new_markdown == self.sidebar_markdown:
            return

        self._sidebar_markdown = new_markdown

        if self._sidebar_markdown is not None:
            self.sidebar_rendered_html = convert_markdown_to_safe_html(new_markdown)
        else:
            self.sidebar_rendered_html = None

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

        # wiki_page_create
        #  - permission must be granted specifically
        acl.append((Allow, "admin", "wiki_page_create"))
        acl.append((Allow, "wiki", "wiki_page_create"))

        acl.append(DENY_ALL)

        return acl

    def is_subgroup_of(self, other: "Group") -> bool:
        """Return whether this group is a sub-group of the other one."""
        # descendant_of() returns True if the ltrees are equal, so avoid that
        if self.path == other.path:
            return False

        return self.path.descendant_of(other.path)
