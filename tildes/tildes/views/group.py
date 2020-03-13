# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to groups."""

from pyramid.request import Request
from pyramid.view import view_config

from tildes.enums import GroupStatType
from tildes.models.group import Group


@view_config(route_name="groups", renderer="groups.jinja2")
def get_list_groups(request: Request) -> dict:
    """Show a list of all groups."""
    groups = request.query(Group).order_by(Group.path).all()

    # converting this to SQLAlchemy seems like way more trouble than it's worth
    posting_stats = request.db_session.execute(
        """
        select path, stat, ceil(sum(value) / count(*))
        from group_stats
            left join groups using (group_id)
        where period && tstzrange(now() - interval '7 days', now())
        group by path, stat
        order by path, stat;
    """
    ).fetchall()

    daily_comment_counts = {
        row[0]: int(row[2])
        for row in posting_stats
        if row[1] == GroupStatType.COMMENTS_POSTED.name
    }

    daily_topic_counts = {
        row[0]: int(row[2])
        for row in posting_stats
        if row[1] == GroupStatType.TOPICS_POSTED.name
    }

    return {
        "groups": groups,
        "daily_comment_counts": daily_comment_counts,
        "daily_topic_counts": daily_topic_counts,
    }
