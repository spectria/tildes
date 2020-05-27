# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Script to post any scheduled topics that are due."""

from typing import Optional

from sqlalchemy.orm.session import Session

from tildes.lib.database import get_session_from_config
from tildes.lib.datetime import utc_now
from tildes.models.topic import TopicSchedule


def _get_next_due_topic(db_session: Session) -> Optional[TopicSchedule]:
    """Get the next due topic (if any).

    Note that this also locks the topic's row with FOR UPDATE as well as using SKIP
    LOCKED. This should (hypothetically) mean that multiple instances of this script
    can run concurrently safely and will not attempt to post the same topics.
    """
    return (
        db_session.query(TopicSchedule)
        .filter(TopicSchedule.next_post_time <= utc_now())  # type: ignore
        .order_by(TopicSchedule.next_post_time)
        .with_for_update(skip_locked=True)
        .first()
    )


def post_scheduled_topics(config_path: str) -> None:
    """Post all scheduled topics that are due to be posted."""
    db_session = get_session_from_config(config_path)

    due_topic = _get_next_due_topic(db_session)

    while due_topic:
        db_session.add(due_topic.create_topic())
        due_topic.advance_schedule_to_future()
        db_session.add(due_topic)
        db_session.commit()

        due_topic = _get_next_due_topic(db_session)
