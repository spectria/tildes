# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Simple script to "officially" close voting on old posts.

This script should be set up to run regularly (such as every hour). It's not totally
essential since the application can generally prevent voting using the same logic, but
the more often it's run, the more correct the is_voting_closed column will be.
"""

from tildes.lib.database import get_session_from_config
from tildes.lib.datetime import utc_now
from tildes.models.comment import Comment, VOTING_PERIOD as COMMENT_VOTING_PERIOD
from tildes.models.topic import Topic, VOTING_PERIOD as TOPIC_VOTING_PERIOD


def close_voting_on_old_posts(config_path: str) -> None:
    """Update is_voting_closed column on all posts older than the voting period."""
    db_session = get_session_from_config(config_path)

    db_session.query(Comment).filter(
        Comment.created_time < utc_now() - COMMENT_VOTING_PERIOD,
        Comment._is_voting_closed == False,  # noqa
    ).update({"_is_voting_closed": True}, synchronize_session=False)

    db_session.query(Topic).filter(
        Topic.created_time < utc_now() - TOPIC_VOTING_PERIOD,
        Topic._is_voting_closed == False,  # noqa
    ).update({"_is_voting_closed": True}, synchronize_session=False)

    db_session.commit()
