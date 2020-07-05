# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the TopicSchedule class."""

from datetime import datetime
from typing import List, Optional

from dateutil.rrule import rrule
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import text

from tildes.lib.database import RecurrenceRule, TagList
from tildes.lib.datetime import utc_now
from tildes.models import DatabaseModel
from tildes.models.group import Group
from tildes.models.topic import Topic
from tildes.models.user import User
from tildes.schemas.topic import TITLE_MAX_LENGTH


class TopicSchedule(DatabaseModel):
    """Model for scheduled topics (auto-posted, often repeatedly on a schedule).

    Trigger behavior:
      Incoming:
        - latest_topic_id will be set when a new topic is inserted for the schedule,
          and updated when a topic from the schedule is deleted or removed.
    """

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
    tags: List[str] = Column(TagList, nullable=False, server_default="{}")
    next_post_time: Optional[datetime] = Column(
        TIMESTAMP(timezone=True), nullable=True, index=True
    )
    recurrence_rule: Optional[rrule] = Column(RecurrenceRule, nullable=True)
    only_new_top_level_comments_in_latest: bool = Column(
        Boolean, nullable=False, server_default="true"
    )
    latest_topic_id: int = Column(Integer, ForeignKey("topics.topic_id"), nullable=True)

    group: Group = relationship("Group", innerjoin=True)
    user: Optional[User] = relationship("User")
    latest_topic: Topic = relationship("Topic", foreign_keys=[latest_topic_id])

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
        self.group = group
        self.title = title
        self.markdown = markdown
        self.tags = tags
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

        # treat both the title and markdown as Jinja templates (sandboxed)
        jinja_sandbox = SandboxedEnvironment()
        jinja_variables = {"current_time_utc": utc_now()}

        try:
            title_template = jinja_sandbox.from_string(self.title)
            title = title_template.render(jinja_variables)
        except:  # pylint: disable=bare-except
            title = self.title

        try:
            markdown_template = jinja_sandbox.from_string(self.markdown)
            markdown = markdown_template.render(jinja_variables)
        except:  # pylint: disable=bare-except
            markdown = self.markdown

        topic = Topic.create_text_topic(self.group, user, title, markdown)
        topic.tags = self.tags
        topic.schedule = self

        return topic

    def advance_schedule_to_future(self) -> None:
        """Advance the schedule to the next future occurrence."""
        if self.recurrence_rule:
            rule = self.recurrence_rule.replace(dtstart=self.next_post_time)
            self.next_post_time = rule.after(utc_now())
        else:
            self.next_post_time = None
