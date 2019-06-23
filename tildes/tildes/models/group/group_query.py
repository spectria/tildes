# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the GroupQuery class."""

from typing import Any

from pyramid.request import Request

from tildes.models import ModelQuery

from .group import Group
from .group_subscription import GroupSubscription


class GroupQuery(ModelQuery):
    """Specialized ModelQuery for Groups."""

    def __init__(self, request: Request):
        """Initialize a GroupQuery for the request.

        If the user is logged in, additional user-specific data will be fetched along
        with the groups. For the moment, this is whether the user is subscribed to them.
        """
        super().__init__(Group, request)

    def _attach_extra_data(self) -> "GroupQuery":
        """Attach the extra user data to the query."""
        if not self.request.user:
            return self

        return self._attach_subscription_data()

    def _attach_subscription_data(self) -> "GroupQuery":
        """Add a subquery to include whether the user is subscribed."""
        subscription_subquery = (
            self.request.query(GroupSubscription)
            .filter(
                GroupSubscription.group_id == Group.group_id,
                GroupSubscription.user == self.request.user,
            )
            .exists()
            .label("user_subscribed")
        )
        return self.add_columns(subscription_subquery)

    @staticmethod
    def _process_result(result: Any) -> Group:
        """Merge additional user-context data in result onto the group."""
        if isinstance(result, Group):
            # the result is already a Group, no merging needed
            group = result
            group.user_subscribed = False
        else:
            group = result.Group
            group.user_subscribed = result.user_subscribed

        return group
