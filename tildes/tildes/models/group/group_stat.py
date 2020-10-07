# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the GroupStat class."""

from datetime import datetime
from typing import Union

from psycopg2.extras import DateTimeTZRange
from sqlalchemy import Column, Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import ENUM, TSTZRANGE
from sqlalchemy.orm import relationship

from tildes.enums import GroupStatType
from tildes.models import DatabaseModel

from .group import Group


class GroupStat(DatabaseModel):
    """Model for a statistic of a group inside a certain time period."""

    __tablename__ = "group_stats"

    group_id: int = Column(
        Integer,
        ForeignKey("groups.group_id"),
        nullable=False,
        primary_key=True,
    )
    stat: GroupStatType = Column(ENUM(GroupStatType), nullable=False, primary_key=True)
    period: DateTimeTZRange = Column(TSTZRANGE, nullable=False, primary_key=True)
    value: float = Column(Float, nullable=False)

    group: Group = relationship("Group", innerjoin=True, lazy=False)

    # Add a GiST index on the period column for range operators
    __table_args__ = (
        Index("ix_group_stats_period_gist", period, postgresql_using="gist"),
    )

    def __init__(
        self,
        group: Group,
        stat: GroupStatType,
        start_time: datetime,
        end_time: datetime,
        value: Union[int, float],
    ):
        """Create a new statistic for the group and time period.

        The time period will be inclusive of start_time but exclusive of end_time.
        """
        self.group = group
        self.stat = stat
        self.period = DateTimeTZRange(start_time, end_time, bounds="[)")
        self.value = float(value)
