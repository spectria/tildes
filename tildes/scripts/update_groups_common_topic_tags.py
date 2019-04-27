# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Script for updating the list of common topic tags for all groups."""

from sqlalchemy import desc, func
from sqlalchemy_utils import Ltree

from tildes.lib.database import get_session_from_config
from tildes.models.group import Group
from tildes.models.topic import Topic


# the maximum number of common tags to store for a particular group
MAX_NUM_COMMON_TAGS = 100


def update_common_topic_tags(config_path: str) -> None:
    """Update the list of common topic tags for all groups."""
    db_session = get_session_from_config(config_path)

    all_groups = db_session.query(Group).all()

    for group in all_groups:
        # create a subquery for all tags from topics in that group - UNNEST() converts
        # the arrays of tags into rows so that we can easily group and count, and
        # created_time will be used to determine when a particular tag was last used
        group_tags = (
            db_session.query(
                func.unnest(Topic._tags).label("tag"), Topic.created_time  # noqa
            )
            .filter(Topic.group == group)
            .subquery()
        )

        # get the list of the most common tags, based on frequency and breaking ties
        # with which was used most recently
        common_tags = (
            db_session.query(
                group_tags.columns["tag"],
                func.count().label("frequency"),
                func.max(group_tags.columns["created_time"]).label("last_used"),
            )
            .group_by("tag")
            .order_by(desc("frequency"), desc("last_used"))
            .limit(MAX_NUM_COMMON_TAGS)
            .all()
        )

        group._common_topic_tags = [  # noqa
            Ltree(common_tag[0]) for common_tag in common_tags
        ]

        db_session.add(group)
        db_session.commit()
