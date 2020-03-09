# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Script for generating group statistics for yesterday (UTC).

This script is not very flexible - no matter what time it is run, it will always
generate stats for the previous UTC day for all groups and store them in the group_stats
table.
"""

from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tildes.enums import GroupStatType
from tildes.lib.database import get_session_from_config
from tildes.lib.datetime import utc_now
from tildes.models.comment import Comment
from tildes.models.group import Group, GroupStat
from tildes.models.topic import Topic


def generate_stats(config_path: str) -> None:
    """Generate all stats for all groups for yesterday (UTC)."""
    db_session = get_session_from_config(config_path)

    # the end time is the start of the current day, start time 1 day before that
    end_time = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(days=1)

    groups = db_session.query(Group).all()

    for group in groups:
        with db_session.no_autoflush:
            db_session.add(topics_posted(db_session, group, start_time, end_time))
            db_session.add(comments_posted(db_session, group, start_time, end_time))

        try:
            db_session.commit()
        except IntegrityError:
            # stats have already run for this group/period combination, just skip
            continue


def topics_posted(
    db_session: Session, group: Group, start_time: datetime, end_time: datetime
) -> GroupStat:
    """Generate a GroupStat for topics posted in the group between start/end times."""
    num_topics = (
        db_session.query(Topic)
        .filter(
            Topic.group == group,
            Topic.created_time >= start_time,
            Topic.created_time < end_time,
            Topic.is_deleted == False,  # noqa
            Topic.is_removed == False,  # noqa
        )
        .count()
    )

    return GroupStat(
        group, GroupStatType.TOPICS_POSTED, start_time, end_time, num_topics
    )


def comments_posted(
    db_session: Session, group: Group, start_time: datetime, end_time: datetime
) -> GroupStat:
    """Generate a GroupStat for comments posted in the group between start/end times."""
    num_comments = (
        db_session.query(Comment)
        .join(Topic)
        .filter(
            Topic.group == group,
            Comment.created_time >= start_time,
            Comment.created_time < end_time,
            Comment.is_deleted == False,  # noqa
            Comment.is_removed == False,  # noqa
        )
        .count()
    )

    return GroupStat(
        group, GroupStatType.COMMENTS_POSTED, start_time, end_time, num_comments
    )
