# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains Pyramid "resource" related code, such as root factories."""

from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound
from pyramid.request import Request

from tildes.models import DatabaseModel, ModelQuery


def get_resource(request: Request, base_query: ModelQuery) -> DatabaseModel:
    """Prepare and execute base query from a root factory, returning result."""
    # pylint: disable=unused-argument
    query = (
        base_query.lock_based_on_request_method()
        .join_all_relationships()
        .undefer_all_columns()
    )

    resource = query.one_or_none()

    if not resource:
        raise HTTPNotFound

    return resource
