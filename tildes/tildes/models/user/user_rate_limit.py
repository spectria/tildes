# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the UserRateLimit class."""

from datetime import timedelta

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Interval, Text
from sqlalchemy.orm import relationship

from tildes.models import DatabaseModel

from .user import User


class UserRateLimit(DatabaseModel):
    """Model for custom rate-limits on actions for individual users."""

    __tablename__ = "user_rate_limit"

    user_id: int = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    action: str = Column(Text, primary_key=True)
    period: timedelta = Column(Interval, nullable=False)
    limit: int = Column(Integer, nullable=False)

    user: User = relationship("User", innerjoin=True)

    def __init__(self, user: User, action: str, period: timedelta, limit: int):
        """Set a new custom rate-limit for a particular user and action."""
        self.user = user
        self.action = action
        self.period = period
        self.limit = limit
