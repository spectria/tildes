# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the UserPermissions class."""

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

from tildes.enums import UserPermission, UserPermissionType
from tildes.models import DatabaseModel
from tildes.models.group import Group
from tildes.models.user import User


class UserPermissions(DatabaseModel):
    """Model for a user's permissions in a group (or all groups)."""

    __tablename__ = "user_permissions"

    permission_id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    group_id: int = Column(Integer, ForeignKey("groups.group_id"), nullable=True)
    permission: UserPermission = Column(ENUM(UserPermission), nullable=False)
    permission_type: UserPermissionType = Column(
        ENUM(UserPermissionType), nullable=False, server_default="ALLOW"
    )

    user: User = relationship("User", innerjoin=True, backref="permissions")
    group: Group = relationship("Group", innerjoin=True)

    @property
    def auth_principal(self) -> str:
        """Return the permission as a string usable as an auth principal.

        The principal is made up of two parts, separated by a colon. The first part is
        the group_id the permission applies to, or a * for all groups. The second part
        is the permission name, prefixed by a ! if the permission is being denied
        instead of allowed:

          - "5:topic.tag" for allowing the topic.tag permission in group id 5
          - "*:topic.tag" for allowing the topic.tag permission in all groups
          - "3:!topic.tag" for denying the topic.tag permission in group id 3
        """
        if self.group_id:
            principal = f"{self.group_id}:"
        else:
            principal = "*:"

        if self.permission_type == UserPermissionType.DENY:
            principal += "!"

        principal += str(self.permission.name)

        return principal
