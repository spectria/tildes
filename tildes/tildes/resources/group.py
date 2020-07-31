# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Root factories for groups."""

from marshmallow.fields import String
from pyramid.httpexceptions import HTTPMovedPermanently, HTTPNotFound
from pyramid.request import Request
from sqlalchemy_utils import Ltree

from tildes.models.group import Group, GroupWikiPage
from tildes.resources import get_resource
from tildes.schemas.group import GroupSchema
from tildes.views.decorators import use_kwargs


@use_kwargs(
    GroupSchema(only=("path",), context={"fix_path_capitalization": True}),
    location="matchdict",
)
def group_by_path(request: Request, path: str) -> Group:
    """Get a group specified by {path} in the route (or 404)."""
    # If loading the specified group path into the GroupSchema changed it, do a 301
    # redirect to the resulting group path. This will happen in cases like the original
    # url including capital letters in the group path, where we want to redirect to the
    # proper all-lowercase path instead.
    if path != request.matchdict["path"]:
        request.matchdict["path"] = path
        proper_url = request.route_url(request.matched_route.name, **request.matchdict)

        raise HTTPMovedPermanently(location=proper_url)

    query = request.query(Group).filter(Group.path == Ltree(path))

    return get_resource(request, query)


@use_kwargs({"wiki_page_path": String()}, location="matchdict")
def group_wiki_page_by_path(request: Request, wiki_page_path: str) -> GroupWikiPage:
    """Get a group's wiki page by its path (or 404)."""
    group = group_by_path(request)  # pylint: disable=no-value-for-parameter

    query = request.query(GroupWikiPage).filter(
        GroupWikiPage.group == group, GroupWikiPage.path == wiki_page_path
    )

    # try to return the page with the exact path, but catch if it doesn't exist
    try:
        return get_resource(request, query)
    except HTTPNotFound:
        pass

    # if it didn't exist, try treating it as a folder and looking for an index page
    wiki_page_path += "/index"
    query = request.query(GroupWikiPage).filter(
        GroupWikiPage.group == group, GroupWikiPage.path == wiki_page_path
    )

    return get_resource(request, query)
