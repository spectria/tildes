"""Root factories for groups."""

from pyramid.httpexceptions import HTTPMovedPermanently
from pyramid.request import Request
from sqlalchemy_utils import Ltree
from webargs.pyramidparser import use_kwargs

from tildes.models.group import Group
from tildes.resources import get_resource
from tildes.schemas.group import GroupSchema


@use_kwargs(
    GroupSchema(only=("path",), context={"fix_path_capitalization": True}),
    locations=("matchdict",),
)
def group_by_path(request: Request, path: str) -> Group:
    """Get a group specified by {group_path} in the route (or 404)."""
    # If loading the specified group path into the GroupSchema changed it, do a 301
    # redirect to the resulting group path. This will happen in cases like the original
    # url including capital letters in the group path, where we want to redirect to the
    # proper all-lowercase path instead.
    if path != request.matchdict["group_path"]:
        request.matchdict["group_path"] = path
        proper_url = request.route_url(request.matched_route.name, **request.matchdict)

        raise HTTPMovedPermanently(location=proper_url)

    query = request.query(Group).filter(Group.path == Ltree(path))

    return get_resource(request, query)
