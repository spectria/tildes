# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the TopicSchedule class."""

from datetime import datetime
from typing import List, Optional

from dateutil.rrule import rrule
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import text
from sqlalchemy_utils import Ltree

from tildes.lib.database import ArrayOfLtree, RecurrenceRule
from tildes.models import DatabaseModel
from tildes.models.group import Group
from tildes.models.topic import Topic
from tildes.models.user import User
from tildes.schemas.topic import TITLE_MAX_LENGTH


class TopicSchedule(DatabaseModel):
    """Model for scheduled topics (auto-posted, often repeatedly on a schedule)."""

    __tablename__ = "topic_schedule"

    schedule_id: int = Column(Integer, primary_key=True)
    group_id: int = Column(
        Integer, ForeignKey("groups.group_id"), nullable=False, index=True
    )
    user_id: Optional[int] = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    created_time: datetime = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    title: str = Column(
        Text,
        CheckConstraint(f"LENGTH(title) <= {TITLE_MAX_LENGTH}", name="title_length"),
        nullable=False,
    )
    markdown: str = Column(Text, nullable=False)
    tags: List[Ltree] = Column(ArrayOfLtree, nullable=False, server_default="{}")
    next_post_time: Optional[datetime] = Column(
        TIMESTAMP(timezone=True), nullable=True, index=True
    )
    recurrence_rule: Optional[rrule] = Column(RecurrenceRule, nullable=True)

    group: Group = relationship("Group", innerjoin=True)
    user: Optional[User] = relationship("User")

    def __init__(
        self,
        group: Group,
        title: str,
        markdown: str,
        tags: List[str],
        next_post_time: datetime,
        recurrence_rule: Optional[rrule] = None,
        user: Optional[User] = None,
    ) -> None:
        """Create a new scheduled topic."""
        # pylint: disable=too-many-arguments
        self.group = group
        self.title = title
        self.markdown = markdown
        self.tags = [Ltree(tag) for tag in tags]
        self.next_post_time = next_post_time
        self.recurrence_rule = recurrence_rule
        self.user = user

    def create_topic(self) -> Topic:
        """Create and return an actual Topic for this scheduled topic."""
        # if no user is specified, use the "generic"/automatic user (ID -1)
        if self.user:
            user = self.user
        else:
            user = (
                Session.object_session(self)
                .query(User)
                .filter(User.user_id == -1)
                .one()
            )

        topic = Topic.create_text_topic(self.group, user, self.title, self.markdown)
        topic.tags = [str(tag) for tag in self.tags]

        return topic

    def advance_schedule(self) -> None:
        """Advance the schedule, setting next_post_time appropriately."""
        if self.recurrence_rule:
            rule = self.recurrence_rule.replace(dtstart=self.next_post_time)
            self.next_post_time = rule.after(self.next_post_time)
        else:
            self.next_post_time = None
