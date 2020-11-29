# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the GroupScript class."""

from typing import Optional

from pyramid.security import DENY_ALL
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from tildes.models import DatabaseModel
from tildes.typing import AclType

from .group import Group


class GroupScript(DatabaseModel):
    """Model for a script in a group, which can be used to process topics/comments."""

    __tablename__ = "group_scripts"

    script_id: int = Column(Integer, primary_key=True)
    group_id: Optional[int] = Column(Integer, ForeignKey("groups.group_id"))
    code: str = Column(Text, nullable=False)

    group: Optional[Group] = relationship("Group")

    def __init__(self, group: Optional[Group], code: str):
        """Create a new script for a group."""
        self.group = group
        self.code = code

    def __acl__(self) -> AclType:
        """Pyramid security ACL."""
        acl = []

        # for now, deny all permissions through the app
        acl.append(DENY_ALL)

        return acl
