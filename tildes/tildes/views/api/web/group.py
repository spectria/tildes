# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Web API endpoints related to groups."""

from typing import Optional

from pyramid.request import Request
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from webargs.pyramidparser import use_kwargs
from zope.sqlalchemy import mark_changed

from tildes.enums import TopicSortOption
from tildes.models.group import Group, GroupSubscription
from tildes.models.user import UserGroupSettings
from tildes.schemas.fields import Enum, ShortTimePeriod
from tildes.views import IC_NOOP
from tildes.views.decorators import ic_view_config


@ic_view_config(
    route_name="group_subscribe",
    request_method="PUT",
    permission="subscribe",
    renderer="group_subscription_box.jinja2",
)
def put_subscribe_group(request: Request) -> dict:
    """Subscribe to a group with Intercooler."""
    group = request.context

    savepoint = request.tm.savepoint()

    new_subscription = GroupSubscription(request.user, group)
    request.db_session.add(new_subscription)

    try:
        # manually flush before attempting to commit, to avoid having all objects
        # detached from the session in case of an error
        request.db_session.flush()
        request.tm.commit()
    except IntegrityError:
        # the user is already subscribed to this group
        savepoint.rollback()

    # re-query the group to get complete data
    group = (
        request.query(Group)
        .join_all_relationships()
        .filter_by(group_id=group.group_id)
        .one()
    )

    return {"group": group}


@ic_view_config(
    route_name="group_subscribe",
    request_method="DELETE",
    permission="subscribe",
    renderer="group_subscription_box.jinja2",
)
def delete_subscribe_group(request: Request) -> dict:
    """Remove the user's subscription from a group with Intercooler."""
    group = request.context

    request.query(GroupSubscription).filter(
        GroupSubscription.group == group, GroupSubscription.user == request.user
    ).delete(synchronize_session=False)

    # manually commit the transaction so triggers will execute
    request.tm.commit()

    # re-query the group to get complete data
    group = (
        request.query(Group)
        .join_all_relationships()
        .filter_by(group_id=group.group_id)
        .one()
    )

    return {"group": group}


@ic_view_config(route_name="group_user_settings", request_method="PATCH")
@use_kwargs(
    {"order": Enum(TopicSortOption), "period": ShortTimePeriod(allow_none=True)}
)
def patch_group_user_settings(
    request: Request, order: TopicSortOption, period: Optional[ShortTimePeriod]
) -> dict:
    """Set the user's default listing options."""
    if period:
        default_period = period.as_short_form()
    else:
        default_period = "all"

    statement = (
        insert(UserGroupSettings.__table__)
        .values(
            user_id=request.user.user_id,
            group_id=request.context.group_id,
            default_order=order,
            default_period=default_period,
        )
        .on_conflict_do_update(
            constraint=UserGroupSettings.__table__.primary_key,
            set_={"default_order": order, "default_period": default_period},
        )
    )
    request.db_session.execute(statement)
    mark_changed(request.db_session)

    return IC_NOOP
