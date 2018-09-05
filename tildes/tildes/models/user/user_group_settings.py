# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the UserGroupSettings class."""

from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

from tildes.enums import TopicSortOption
from tildes.models import DatabaseModel
from tildes.models.group import Group
from tildes.models.user import User


class UserGroupSettings(DatabaseModel):
    """Model for a user's settings related to a specific group."""

    __tablename__ = "user_group_settings"

    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    group_id: int = Column(
        Integer, ForeignKey("groups.group_id"), nullable=False, primary_key=True
    )
    default_order: Optional[TopicSortOption] = Column(ENUM(TopicSortOption))
    default_period: Optional[str] = Column(Text)

    user: User = relationship("User", innerjoin=True)
    group: Group = relationship("Group", innerjoin=True)
