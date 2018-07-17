"""Contains Pyramid "resource" related code, such as root factories."""

from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound
from pyramid.request import Request

from tildes.models import DatabaseModel, ModelQuery


def get_resource(request: Request, base_query: ModelQuery) -> DatabaseModel:
    """Prepare and execute base query from a root factory, returning result."""
    # While the site is private, we don't want to leak information about which
    # usernames or groups exist. So we should just always raise a 403 before
    # doing a lookup and potentially raising a 404.
    if not request.user:
        raise HTTPForbidden

    query = (
        base_query
        .lock_based_on_request_method()
        .join_all_relationships()
    )

    if not request.is_safe_method:
        query = query.undefer_all_columns()

    resource = query.one_or_none()

    if not resource:
        raise HTTPNotFound

    return resource
