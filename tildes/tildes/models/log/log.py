# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the Log class."""
# pylint: disable=too-many-branches,too-many-return-statements

from typing import Any, Dict, Optional

from pyramid.request import Request
from sqlalchemy import BigInteger, Column, event, ForeignKey, Integer, Table, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM, INET, JSONB
from sqlalchemy.engine import Connection
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tildes.enums import LogEventType
from tildes.models import DatabaseModel
from tildes.models.comment import Comment
from tildes.models.topic import Topic


class BaseLog:
    """Mixin class with the shared columns/relationships for log classes."""

    @declared_attr
    def log_id(self) -> Column:
        """Return the log_id column."""
        return Column(BigInteger, primary_key=True)

    @declared_attr
    def user_id(self) -> Column:
        """Return the user_id column."""
        return Column(Integer, ForeignKey("users.user_id"), index=True)

    @declared_attr
    def event_type(self) -> Column:
        """Return the event_type column."""
        return Column(ENUM(LogEventType), nullable=False, index=True)

    @declared_attr
    def ip_address(self) -> Column:
        """Return the ip_address column."""
        return Column(INET, nullable=False, index=True)

    @declared_attr
    def event_time(self) -> Column:
        """Return the event_time column."""
        return Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            index=True,
            server_default=text("NOW()"),
        )

    @declared_attr
    def info(self) -> Column:
        """Return the info column."""
        return Column(MutableDict.as_mutable(JSONB(none_as_null=True)))

    @declared_attr
    def user(self) -> Any:
        """Return the user relationship."""
        return relationship("User", lazy=False)


class Log(DatabaseModel, BaseLog):
    """Model for a basic log entry."""

    __tablename__ = "log"

    INHERITED_TABLES = ["log_comments", "log_topics"]

    def __init__(
        self,
        event_type: LogEventType,
        request: Request,
        info: Optional[Dict[str, Any]] = None,
    ):
        """Create a new log entry.

        User and IP address info is extracted from the Request object. `info` is an
        optional dict of arbitrary data that will be stored in JSON form.
        """
        self.user = request.user
        self.event_type = event_type
        self.ip_address = request.client_addr

        if info:
            self.info = info


class LogComment(DatabaseModel, BaseLog):
    """Model for a log entry related to a specific comment."""

    __tablename__ = "log_comments"

    comment_id: int = Column(
        Integer, ForeignKey("comments.comment_id"), index=True, nullable=False
    )

    comment: Comment = relationship("Comment")

    def __init__(
        self,
        event_type: LogEventType,
        request: Request,
        comment: Comment,
        info: Optional[Dict[str, Any]] = None,
    ):
        """Create a new log entry related to a specific comment."""
        # pylint: disable=non-parent-init-called
        Log.__init__(self, event_type, request, info)

        self.comment = comment

    def __str__(self) -> str:
        """Return a string representation of the log event."""
        return f"performed action {self.event_type.name}"


class LogTopic(DatabaseModel, BaseLog):
    """Model for a log entry related to a specific topic."""

    __tablename__ = "log_topics"

    topic_id: int = Column(
        Integer, ForeignKey("topics.topic_id"), index=True, nullable=False
    )

    topic: Topic = relationship("Topic")

    def __init__(
        self,
        event_type: LogEventType,
        request: Request,
        topic: Topic,
        info: Optional[Dict[str, Any]] = None,
    ):
        """Create a new log entry related to a specific topic."""
        # pylint: disable=non-parent-init-called
        Log.__init__(self, event_type, request, info)

        self.topic = topic

    def __str__(self) -> str:
        """Return a string representation of the log event."""
        if self.event_type == LogEventType.TOPIC_TAG:
            return self._tag_event_description()
        elif self.event_type == LogEventType.TOPIC_MOVE:
            old_group = self.info["old"]
            new_group = self.info["new"]
            return f"moved from ~{old_group} to ~{new_group}"
        elif self.event_type == LogEventType.TOPIC_LOCK:
            return "locked comments"
        elif self.event_type == LogEventType.TOPIC_REMOVE:
            return "removed"
        elif self.event_type == LogEventType.TOPIC_UNLOCK:
            return "unlocked comments"
        elif self.event_type == LogEventType.TOPIC_UNREMOVE:
            return "un-removed"
        elif self.event_type == LogEventType.TOPIC_TITLE_EDIT:
            old_title = self.info["old"]
            new_title = self.info["new"]
            return f'changed title from "{old_title}" to "{new_title}"'
        elif self.event_type == LogEventType.TOPIC_LINK_EDIT:
            old_link = self.info["old"]
            new_link = self.info["new"]
            return f"changed link from {old_link} to {new_link}"

        return f"performed action {self.event_type.name}"

    def _tag_event_description(self) -> str:
        """Return a description of a TOPIC_TAG event as a string."""
        if self.event_type != LogEventType.TOPIC_TAG:
            raise TypeError

        old_tags = set(self.info["old"])
        new_tags = set(self.info["new"])

        added_tags = new_tags - old_tags
        removed_tags = old_tags - new_tags

        description = ""
        if added_tags:
            tag_str = ", ".join([f"'{tag}'" for tag in added_tags])
            if len(added_tags) == 1:
                description += f"added tag {tag_str}"
            else:
                description += f"added tags {tag_str}"

            if removed_tags:
                description += " and "

        if removed_tags:
            tag_str = ", ".join([f"'{tag}'" for tag in removed_tags])
            if len(removed_tags) == 1:
                description += f"removed tag {tag_str}"
            else:
                description += f"removed tags {tag_str}"

        return description


@event.listens_for(Log.__table__, "after_create")
def create_inherited_tables(
    target: Table, connection: Connection, **kwargs: Any
) -> None:
    """Create all the tables that inherit from the base "log" one."""
    # pylint: disable=unused-argument
    naming = DatabaseModel.metadata.naming_convention

    # log_topics
    connection.execute(
        "CREATE TABLE log_topics (topic_id integer not null) INHERITS (log)"
    )

    fk_name = naming["fk"] % {
        "table_name": "log_topics",
        "column_0_name": "topic_id",
        "referred_table_name": "topics",
    }
    connection.execute(
        f"ALTER TABLE log_topics ADD CONSTRAINT {fk_name} "
        "FOREIGN KEY (topic_id) REFERENCES topics (topic_id)"
    )

    ix_name = naming["ix"] % {"table_name": "log_topics", "column_0_name": "topic_id"}
    connection.execute(f"CREATE INDEX {ix_name} ON log_topics (topic_id)")

    # log_comments
    connection.execute(
        "CREATE TABLE log_comments (comment_id integer not null) INHERITS (log)"
    )

    fk_name = naming["fk"] % {
        "table_name": "log_comments",
        "column_0_name": "comment_id",
        "referred_table_name": "comments",
    }
    connection.execute(
        f"ALTER TABLE log_comments ADD CONSTRAINT {fk_name} "
        "FOREIGN KEY (comment_id) REFERENCES comments (comment_id)"
    )

    ix_name = naming["ix"] % {
        "table_name": "log_comments",
        "column_0_name": "comment_id",
    }
    connection.execute(f"CREATE INDEX {ix_name} ON log_comments (comment_id)")

    # duplicate all the indexes/constraints from the base log table
    for table in Log.INHERITED_TABLES:
        pk_name = naming["pk"] % {"table_name": table}
        connection.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT {pk_name} PRIMARY KEY (log_id)"
        )

        for col in ("event_time", "event_type", "ip_address", "user_id"):
            ix_name = naming["ix"] % {"table_name": table, "column_0_name": col}
            connection.execute(f"CREATE INDEX {ix_name} ON {table} ({col})")

        fk_name = naming["fk"] % {
            "table_name": table,
            "column_0_name": "user_id",
            "referred_table_name": "users",
        }
        connection.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT {fk_name} "
            "FOREIGN KEY (user_id) REFERENCES users (user_id)"
        )
