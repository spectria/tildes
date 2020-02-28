# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the UserPermissions class."""

from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

from tildes.enums import UserPermissionType
from tildes.models import DatabaseModel
from tildes.models.group import Group
from tildes.models.user import User


class UserPermissions(DatabaseModel):
    """Model for a user's permissions in a group (or all groups)."""

    __tablename__ = "user_permissions"

    permission_id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    group_id: int = Column(Integer, ForeignKey("groups.group_id"), nullable=True)
    permission: str = Column(Text, nullable=False)
    permission_type: UserPermissionType = Column(
        ENUM(UserPermissionType), nullable=False, server_default="ALLOW"
    )

    user: User = relationship("User", innerjoin=True, backref="permissions")
    group: Group = relationship("Group", innerjoin=True)

    @property
    def auth_principal(self) -> str:
        """Return the permission as a string usable as an auth principal.

        WARNING: This isn't currently complete, and only handles ALLOW for all groups.
        """
        if self.permission_type != UserPermissionType.ALLOW:
            raise ValueError("Not an ALLOW permission.")

        if self.group_id:
            raise ValueError("Not an all-groups permission.")

        return self.permission
